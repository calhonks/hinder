from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..deps import get_db
from ..db.models import MatchLog

router = APIRouter(prefix="/feedback", tags=["feedback"]) 


@router.post("")
async def post_feedback(user_id: str, candidate_id: str, feedback: str, db: Session = Depends(get_db)):
    log = MatchLog(user_id=user_id, candidate_id=candidate_id, feedback=feedback)
    db.add(log)
    db.commit()
    return {"ok": True}
