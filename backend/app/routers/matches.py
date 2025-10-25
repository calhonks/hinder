from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlmodel import Session
from ..deps import get_db
from ..db.models import Profile, MatchLog
from ..services.matching import retrieve_candidates, blend_scores
from ..services.explanations import rationale
from ..utils.json import json_to_list

router = APIRouter(prefix="/matches", tags=["matches"]) 


def prof_to_dict(p: Profile) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "headline": p.headline,
        "skills_norm": json_to_list(p.skills_norm_json),
        "topics": json_to_list(p.topics_json),
        "available_now": p.available_now,
        "hackathon": p.hackathon,
    }


@router.get("")
async def get_matches(user_id: str, k: int = 20, topic: Optional[str] = None, hackathon: Optional[str] = None, db: Session = Depends(get_db)):
    user = db.get(Profile, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ids, metas, dists = retrieve_candidates(prof_to_dict(user), k=k, topic=topic, exclude_id=user_id, hackathon=hackathon)
    sv, sk, sb = blend_scores(prof_to_dict(user), metas, dists)

    # fetch candidate profiles to return full shape expected by frontend
    out_matches = []
    for i, cid in enumerate(ids[:k]):
        p = db.get(Profile, cid)
        if not p:
            continue
        cand = {
            "id": p.id,
            "name": p.name,
            "headline": p.headline,
            "email": p.email,
            "school": p.school,
            "company": p.company,
            "seniority": p.seniority,
            "linkedin_url": p.linkedin_url,
            "resume_file_id": p.resume_file_id,
            "resume_file_name": p.resume_file_name,
            "skills_norm": json_to_list(p.skills_norm_json),
            "interests": json_to_list(p.interests_json),
            "topics": json_to_list(p.topics_json),
            "available_now": p.available_now,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "hackathon": p.hackathon,
        }
        overlap = {
            "skills": list(set(json_to_list(user.skills_norm_json)) & set(cand["skills_norm"])),
            "topics": list(set(json_to_list(user.topics_json)) & set(cand["topics"]))
        }
        why = rationale(prof_to_dict(user), cand, overlap)
        out_matches.append({
            "user_id": user_id,
            "candidate": cand,
            "score_vector": sv[i],
            "score_keyword": sk[i],
            "score_blended": sb[i],
            "rationale": why,
        })

    return {"matches": out_matches}
