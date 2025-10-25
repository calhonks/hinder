from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProfileModel(BaseModel):
    id: str
    name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    school: Optional[str] = None
    company: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_file_id: Optional[str] = None
    resume_file_name: Optional[str] = None
    skills_norm: List[str] = []
    interests: List[str] = []
    topics: List[str] = []
    available_now: bool = False
    created_at: str
    updated_at: str
    hackathon: Optional[str] = None


class CreateProfileInput(BaseModel):
    consent: bool
    linkedin_url: Optional[str] = None
    resume_file_id: Optional[str] = None
    resume_file_name: Optional[str] = None
    topics: List[str]
    available_now: bool
    hackathon: Optional[str] = None


class ProfileWithStatus(BaseModel):
    profile: ProfileModel
    status: str


class PatchProfileInput(BaseModel):
    name: Optional[str] = None
    headline: Optional[str] = None
    topics: Optional[List[str]] = None
    available_now: Optional[bool] = None
    skills_norm: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    resume_file_id: Optional[str] = None
    resume_file_name: Optional[str] = None
    hackathon: Optional[str] = None
