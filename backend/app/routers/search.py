from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List
from sqlmodel import Session, select
from ..deps import get_db
from ..db.models import Profile
from ..services.embeddings import embed
from ..services.chroma_store import query as chroma_query
from ..utils.json import json_to_list
from ..services.auth import decode_token

router = APIRouter(prefix="/search", tags=["search"]) 


def _csv_list(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _profile_to_min(p: Profile) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "headline": p.headline,
        "skills_norm": json_to_list(p.skills_norm_json),
        "topics": json_to_list(p.topics_json),
        "available_now": p.available_now,
        "hackathon": p.hackathon,
        "school": p.school,
        "company": p.company,
        "city": p.city if hasattr(p, "city") else None,
        "country_code": p.country_code if hasattr(p, "country_code") else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
async def search(
    q: Optional[str] = None,
    skills: Optional[str] = None,
    topics: Optional[str] = None,
    available_now: Optional[bool] = None,
    city: Optional[str] = None,
    country_code: Optional[str] = None,
    company: Optional[str] = None,
    school: Optional[str] = None,
    hackathon: Optional[str] = None,
    exclude_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    # Require auth
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    if not decode_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    skills_lst = _csv_list(skills)
    topics_lst = _csv_list(topics)

    # Build a query text from filters if q not provided
    query_text_parts: List[str] = []
    if q:
        query_text_parts.append(q)
    query_text_parts.extend(skills_lst)
    query_text_parts.extend(topics_lst)
    for f in (company, school, city, country_code, hackathon):
        if f:
            query_text_parts.append(f)
    # Ensure we always have something to embed
    search_text = " | ".join([p for p in query_text_parts if p]) or "general candidate search"

    vec = embed(search_text)

    # We over-fetch and then filter in Python since some metadata fields are JSON-encoded for Chroma
    n_results = max(page_size * 5, 50)
    where = {}
    # Simple primitive filters that we know are primitives in Chroma metadata
    if available_now is not None:
        where["available_now"] = bool(available_now)
    if company:
        where["company"] = company
    if school:
        where["school"] = school
    if city:
        where["city"] = city
    if country_code:
        where["country_code"] = country_code
    if hackathon:
        where["hackathon"] = hackathon
    where_not = {"id": exclude_id} if exclude_id else None

    res = chroma_query(vec, n_results=n_results, where=where or None, where_not=where_not)

    ids: List[str] = res.get("ids", [[]])[0]
    # Post-filter by skills/topics overlap when provided
    filtered: List[str] = []
    for pid in ids:
        p = db.get(Profile, pid)
        if not p:
            continue
        # skills/topics filter (array containment via Python)
        if skills_lst:
            prof_sk = set(json_to_list(p.skills_norm_json))
            if not any(s.lower() in (x.lower() for x in prof_sk) for s in skills_lst):
                continue
        if topics_lst:
            prof_tp = set(json_to_list(p.topics_json))
            if not any(t.lower() in (x.lower() for x in prof_tp) for t in topics_lst):
                continue
        filtered.append(pid)

    total = len(filtered)
    start = max((page - 1) * page_size, 0)
    end = start + page_size
    page_ids = filtered[start:end]

    items = []
    for pid in page_ids:
        p = db.get(Profile, pid)
        if p:
            items.append(_profile_to_min(p))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "query_text": search_text,
    }
