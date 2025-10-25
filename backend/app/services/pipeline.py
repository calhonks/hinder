from __future__ import annotations
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from ..db.models import Profile, Upload
from .pdf import extract_text
from .parsing import extract as parse_extract
from .normalize import normalize_list
from .embeddings import embed
from .chroma_store import upsert as chroma_upsert, delete as chroma_delete
from .sse import broker
from datetime import datetime


def _json_list(s: Optional[str]) -> List[str]:
    import json
    try:
        return list(json.loads(s or "[]"))
    except Exception:
        return []


def _list_json(lst: Optional[List[str]]) -> str:
    import json
    return json.dumps(lst or [])


def _summary(profile: Profile) -> str:
    skills = ", ".join(_json_list(profile.skills_norm_json))
    topics = ", ".join(_json_list(profile.topics_json))
    return f"{profile.name or ''} | {profile.headline or ''} | {skills} | {topics}"


async def run(db: Session, profile_id: str) -> None:
    prof = db.get(Profile, profile_id)
    if not prof:
        return
    try:
        prof.status = "parsing"
        db.add(prof)
        db.commit()
        await broker.publish(profile_id, {"status": "parsing"})

        raw_text_parts: List[str] = []

        # ingest PDF if present
        if prof.resume_file_id:
            up = db.get(Upload, prof.resume_file_id)
            if up and up.path:
                raw_text_parts.append(extract_text(up.path))

        # ingest from linkedin url via brightdata later (stubbed)

        raw_text = "\n".join([p for p in raw_text_parts if p])

        parsed = await parse_extract(raw_text)

        # update basic fields (best-effort)
        prof.name = prof.name or parsed.get("name")
        prof.headline = prof.headline or parsed.get("headline")
        tech = parsed.get("skills", {}).get("tech", [])
        domain = parsed.get("skills", {}).get("domain", [])
        skills_norm = normalize_list(list(set((_json_list(prof.skills_norm_json) + tech + domain))))
        topics = normalize_list(list(set((_json_list(prof.topics_json)))))
        prof.skills_norm_json = _list_json(skills_norm)
        prof.topics_json = _list_json(topics)

        prof.status = "embedding"
        prof.updated_at = datetime.utcnow()
        db.add(prof)
        db.commit()
        await broker.publish(profile_id, {"status": "embedding"})

        # build summary and embed
        summary = _summary(prof)
        vec = embed(summary)

        metadata = {
            "id": prof.id,
            "name": prof.name,
            "headline": prof.headline,
            "skills_norm": skills_norm,
            "topics": topics,
            "school": prof.school,
            "company": prof.company,
            "seniority": prof.seniority,
            "available_now": prof.available_now,
            "hackathon": prof.hackathon,
        }
        chroma_upsert(profile_id, vec, metadata)

        prof.status = "ready"
        prof.updated_at = datetime.utcnow()
        db.add(prof)
        db.commit()
        await broker.publish(profile_id, {"status": "ready"})

    except Exception:
        prof = db.get(Profile, profile_id)
        if prof:
            prof.status = "error"
            db.add(prof)
            db.commit()
        await broker.publish(profile_id, {"status": "error"})


def delete_profile_index(profile_id: str) -> None:
    try:
        chroma_delete(profile_id)
    except Exception:
        pass
