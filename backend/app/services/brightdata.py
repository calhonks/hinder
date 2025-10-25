from __future__ import annotations
from typing import Dict, Any
from ..config import BRIGHTDATA_ENABLED

# Stub enrichment service. Real integration can use brightdatatest flow.

async def enrich_profile(linkedin_url: str) -> Dict[str, Any]:
    if not BRIGHTDATA_ENABLED:
        return {"enriched": False, "data": None}
    # Placeholder fake enrichment
    fake = {
        "skills": ["linkedin", "public-profile"],
        "companies": ["Some Co"],
    }
    return {"enriched": True, "data": fake}
