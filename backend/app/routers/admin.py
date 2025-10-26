from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from ..deps import get_db
from ..db.models import Profile, MatchLog, User
from ..services.seeding import generate_synthetic_profiles
from ..services.auth import decode_token

router = APIRouter(prefix="/admin", tags=["admin"]) 


def _require_admin(authorization: str | None, db: Session) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = data.get("sub")
    try:
        user = db.get(User, int(uid))
    except Exception:
        user = None
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    _require_admin(authorization, db)
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
async def seed(count: int = 12, db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    _require_admin(authorization, db)
    added = generate_synthetic_profiles(db, count=count)
    return {"added": added}


@router.post("/clear")
async def clear_cache(db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    _require_admin(authorization, db)
    # Reset feedback; keep profiles
    logs = db.exec(select(MatchLog)).all()
    for l in logs:
        db.delete(l)
    db.commit()
    return {"ok": True}
