from __future__ import annotations
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Header
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from ..deps import get_db
from ..db.models import Profile, User
from ..services.brightdata import enrich_profile
from ..services.normalize import normalize_list
from ..services.embeddings import embed
from ..services.chroma_store import upsert as chroma_upsert
from ..db.session import get_session
from ..utils.json import json_to_list, list_to_json
import threading
import asyncio
from typing import Optional
from ..services.auth import decode_token

router = APIRouter(prefix="/brightdata", tags=["brightdata"]) 


def _merge_enrichment_and_reindex(profile_id: str, linkedin_url: str) -> None:
    # Fresh DB session inside background task
    db: Session = get_session()
    try:
        p = db.get(Profile, profile_id)
        if not p:
            return
        # Call provider (may take minutes). Safe to use asyncio.run in this worker thread.
        res = asyncio.run(enrich_profile(linkedin_url))
        if not res.get("enriched"):
            print("Error enriching profile", res)
            return
        data = res.get("data") or {}
        print("BrightData raw data:", data)
        # Backfill key Profile fields when missing
        if not p.linkedin_url:
            p.linkedin_url = linkedin_url
        if not p.name:
            p.name = data.get("name") or (f"{data.get('first_name','')} {data.get('last_name','')}".strip() or None)
        if not p.headline:
            p.headline = data.get("position")
        if not p.company and isinstance(data.get("current_company"), dict):
            p.company = data.get("current_company", {}).get("name")
        if not p.school and isinstance(data.get("education"), list) and data["education"]:
            first_ed = data["education"][0]
            p.school = first_ed.get("title")

        # Extract skills from possible shapes: list of strings, list of dicts with 'name', or alt keys
        def _extract_skills(d: dict) -> list:
            candidates = []
            for key in ["skills", "top_skills", "skills_list"]:
                val = d.get(key)
                if isinstance(val, list):
                    candidates.extend(val)
            # If nested structures exist
            flat = []
            for item in candidates:
                if isinstance(item, str):
                    flat.append(item)
                elif isinstance(item, dict):
                    for k in ("name", "skill", "title"):
                        if item.get(k):
                            flat.append(str(item.get(k)))
                            break
            # Fallback derivation when no explicit skills present
            if not flat:
                derived = []
                # Titles from experience
                for exp in d.get("experience", []) or []:
                    if isinstance(exp, dict):
                        if isinstance(exp.get("positions"), list):
                            for pos in exp["positions"]:
                                if isinstance(pos, dict) and pos.get("title"):
                                    derived.append(pos["title"]) 
                        if exp.get("title"):
                            derived.append(exp["title"])
                        if exp.get("description"):
                            derived.append(exp["description"])  # keep phrases; normalize_list will clean
                # Education fields / degrees
                for ed in d.get("education", []) or []:
                    if isinstance(ed, dict):
                        for k in ("field", "degree", "title"):
                            if ed.get(k):
                                derived.append(ed[k])
                # Certifications titles
                for cert in d.get("certifications", []) or []:
                    if isinstance(cert, dict) and cert.get("title"):
                        derived.append(cert["title"])
                # Headline/position
                if d.get("position"):
                    derived.append(d["position"])
                flat = derived
            return flat

        new_skills = _extract_skills(data)
        if not new_skills:
            print("BrightData enrichment returned no skills. Data keys:", list(data.keys()))
        skills = normalize_list(list(set(json_to_list(p.skills_norm_json) + new_skills)))
        if not skills:
            print("After merge/normalize, skills still empty for profile", profile_id)
        p.skills_norm_json = list_to_json(skills)
        p.updated_at = datetime.now(timezone.utc)
        p.last_linkedin_enrich_at = datetime.now(timezone.utc)
        db.add(p)
        db.commit()

        # Re-embed and upsert to Chroma
        summary = f"{p.name or ''} | {p.headline or ''} | {', '.join(skills)} | {', '.join(json_to_list(p.topics_json))}"
        try:
            vec = embed(summary)
            metadata = {
                "id": p.id,
                "name": p.name,
                "headline": p.headline,
                "skills_norm": skills,
                "topics": json_to_list(p.topics_json),
                "school": p.school,
                "company": p.company,
                "seniority": p.seniority,
                "available_now": p.available_now,
                "hackathon": p.hackathon,
                "city": data.get("city"),
                "country_code": data.get("country_code"),
            }
            chroma_upsert(p.id, vec, metadata)
        except Exception as e:
            print("Embedding/Chroma upsert failed:", type(e).__name__, str(e))
    finally:
        db.close()


@router.post("/enrich")
async def enrich(
    payload: dict,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    # Require auth
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Optionally fetch user if needed later
    uid = data.get("sub")
    try:
        _ = db.get(User, int(uid))
    except Exception:
        _ = None
    if _ is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    linkedin_url = payload.get("linkedin_url")
    profile_id = payload.get("profile_id")
    if not linkedin_url or not profile_id:
        raise HTTPException(status_code=400, detail="linkedin_url and profile_id are required")

    p = db.get(Profile, profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Ownership enforcement: profile must belong to current user.
    # If profile has no owner yet, claim it to current user for backward compatibility.
    if p.user_id is None:
        try:
            p.user_id = int(uid)
            db.add(p)
            db.commit()
        except Exception:
            pass
    elif str(p.user_id) != str(uid):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Rate limit: once per 24h
    if p.last_linkedin_enrich_at and (datetime.utcnow() - p.last_linkedin_enrich_at) < timedelta(days=1):
        return {"accepted": False, "reason": "rate_limited", "next_allowed_at": (p.last_linkedin_enrich_at + timedelta(days=1)).isoformat()}

    # Schedule background enrichment in a separate thread; return immediately
    def _starter(pid: str, url: str) -> None:
        t = threading.Thread(target=_merge_enrichment_and_reindex, args=(pid, url), daemon=True)
        t.start()

    background.add_task(_starter, profile_id, linkedin_url)
    return {"accepted": True}
