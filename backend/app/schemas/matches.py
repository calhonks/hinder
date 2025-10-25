from __future__ import annotations
from pydantic import BaseModel
from typing import List
from .profiles import ProfileModel


class Match(BaseModel):
    user_id: str
    candidate: ProfileModel
    score_vector: float
    score_keyword: float
    score_blended: float
    rationale: str
