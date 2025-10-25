from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..deps import get_db
from ..db.models import Profile, MatchLog
from ..services.seeding import generate_synthetic_profiles

router = APIRouter(prefix="/admin", tags=["admin"]) 


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    profiles = db.exec(select(Profile)).all()
    matches_served = db.exec(select(MatchLog)).all()
    good = len([m for m in matches_served if m.feedback == "good"])
    meh = len([m for m in matches_served if m.feedback == "meh"])
    bad = len([m for m in matches_served if m.feedback == "bad"])
    total = good + meh + bad
    positive_rate = (good / total) if total else 0.0
    return {
        "profiles": len(profiles),
        "matchesServed": len(matches_served),
        "feedback": {"good": good, "meh": meh, "bad": bad, "positiveRate": positive_rate},
    }


@router.post("/seed")
async def seed(count: int = 12, db: Session = Depends(get_db)):
    added = generate_synthetic_profiles(db, count=count)
    return {"added": added}


@router.post("/clear")
async def clear_cache(db: Session = Depends(get_db)):
    # Reset feedback; keep profiles
    logs = db.exec(select(MatchLog)).all()
    for l in logs:
        db.delete(l)
    db.commit()
    return {"ok": True}
