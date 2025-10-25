from __future__ import annotations
from fastapi import APIRouter
from ..services.brightdata import enrich_profile

router = APIRouter(prefix="/brightdata", tags=["brightdata"]) 


@router.post("/enrich")
async def enrich(payload: dict):
    linkedin_url = payload.get("linkedin_url")
    profile_id = payload.get("profile_id")
    if not linkedin_url:
        return {"enriched": False, "error": "linkedin_url required"}
    res = await enrich_profile(linkedin_url)
    return res
