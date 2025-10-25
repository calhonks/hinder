from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
import json


class Upload(SQLModel, table=True):
    file_id: str = Field(primary_key=True)
    path: str
    mime: str
    size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Profile(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    school: Optional[str] = None
    company: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_file_id: Optional[str] = None
    resume_file_name: Optional[str] = None
    skills_norm_json: str = Field(default_factory=lambda: json.dumps([]))
    interests_json: str = Field(default_factory=lambda: json.dumps([]))
    topics_json: str = Field(default_factory=lambda: json.dumps([]))
    available_now: bool = Field(default=False)
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    hackathon: Optional[str] = None


class MatchLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    candidate_id: str
    score_vector: Optional[float] = None
    score_keyword: Optional[float] = None
    score_blended: Optional[float] = None
    rationale: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Intro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_id: str
    to_id: str
    message: str
    delivered: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
