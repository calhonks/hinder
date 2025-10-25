from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from ..deps import get_db
from ..db.models import Profile, Intro
from ..services.explanations import icebreaker
from ..utils.json import json_to_list

router = APIRouter(prefix="/intro", tags=["intro"]) 


def prof_to_dict(p: Profile) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "headline": p.headline,
        "skills_norm": json_to_list(p.skills_norm_json),
        "topics": json_to_list(p.topics_json),
    }


@router.post("")
async def post_intro(payload: dict, db: Session = Depends(get_db)):
    from_id = payload.get("from_id")
    to_id = payload.get("to_id")
    if not from_id or not to_id:
        raise HTTPException(status_code=400, detail="from_id and to_id are required")

    u = db.get(Profile, from_id)
    v = db.get(Profile, to_id)
    if not u or not v:
        raise HTTPException(status_code=404, detail="profile not found")

    overlap = {
        "skills": list(set(json_to_list(u.skills_norm_json)) & set(json_to_list(v.skills_norm_json))),
        "topics": list(set(json_to_list(u.topics_json)) & set(json_to_list(v.topics_json))),
    }
    out = icebreaker(prof_to_dict(u), prof_to_dict(v), overlap)

    intro = Intro(from_id=from_id, to_id=to_id, message=out["message"], delivered=False)
    db.add(intro)
    db.commit()

    return {"message": out["message"], "rationale": out["rationale"]}
