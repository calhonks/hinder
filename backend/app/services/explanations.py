from __future__ import annotations
from typing import Dict

_cache: dict[tuple[str, str], Dict[str, str]] = {}


def rationale(user: Dict, candidate: Dict, overlap: Dict) -> str:
    key = (user.get("id"), candidate.get("id"))
    if key in _cache:
        return _cache[key]["rationale"]
    skills = ", ".join((overlap.get("skills") or [])[:2])
    topics = ", ".join((overlap.get("topics") or [])[:1])
    msg = f"Overlap on {topics or 'interests'} and skills {skills or 'similar areas'}."
    _cache[key] = {"rationale": msg}
    return msg


def icebreaker(user: Dict, candidate: Dict, overlap: Dict) -> Dict[str, str]:
    key = (user.get("id"), candidate.get("id"))
    if key in _cache and _cache[key].get("message"):
        return _cache[key]
    topics = ", ".join((overlap.get("topics") or [])[:1])
    skills = ", ".join((overlap.get("skills") or [])[:1])
    message = f"Hi {candidate.get('name') or 'there'} — noticed we both care about {topics or skills}. Want to team up?"
    why = rationale(user, candidate, overlap)
    _cache[key] = {"message": message, "rationale": why}
    return _cache[key]
