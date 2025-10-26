from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session
from ..deps import get_db
from ..db.models import MatchLog

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackInput(BaseModel):
    user_id: str
    candidate_id: str
    feedback: str


@router.post("")
async def post_feedback(input: FeedbackInput, db: Session = Depends(get_db)):
    log = MatchLog(user_id=input.user_id, candidate_id=input.candidate_id, feedback=input.feedback)
    db.add(log)
    db.commit()
    return {"ok": True}
