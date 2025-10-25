from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import asyncio
import json
from ..deps import get_db
from ..db.models import Profile
from ..schemas.common import ParseStatusResponse
from ..services.sse import broker

router = APIRouter(prefix="/status", tags=["status"]) 


@router.get("")
async def get_status(profile_id: str, db: Session = Depends(get_db)):
    p = db.get(Profile, profile_id)
    return ParseStatusResponse(status=p.status if p else "error")


@router.get("/stream")
async def status_stream(request: Request, profile_id: str):
    q = broker.subscribe(profile_id)

    async def event_generator():
        try:
            # initial heartbeat
            yield "event: heartbeat\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15.0)
                    payload = json.dumps(data)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield "event: heartbeat\n\n"
        finally:
            broker.unsubscribe(profile_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
