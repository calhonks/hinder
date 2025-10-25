from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from datetime import datetime
from typing import Optional
from ..deps import get_db
from ..db.models import Profile, Upload
from ..schemas.profiles import CreateProfileInput, ProfileWithStatus, ProfileModel, PatchProfileInput
from ..services.pipeline import run as pipeline_run, delete_profile_index
from ..utils.ids import new_id
from ..utils.json import list_to_json, json_to_list
from ..config import UPLOAD_DIR
import os

router = APIRouter(prefix="/profiles", tags=["profiles"]) 


def to_model(p: Profile) -> ProfileModel:
    return ProfileModel(
        id=p.id,
        name=p.name,
        headline=p.headline,
        email=p.email,
        school=p.school,
        company=p.company,
        seniority=p.seniority,
        linkedin_url=p.linkedin_url,
        resume_file_id=p.resume_file_id,
        resume_file_name=p.resume_file_name,
        skills_norm=json_to_list(p.skills_norm_json),
        interests=json_to_list(p.interests_json),
        topics=json_to_list(p.topics_json),
        available_now=p.available_now,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
        hackathon=p.hackathon,
    )


@router.post("", response_model=ProfileWithStatus)
async def create_profile(input: CreateProfileInput, background: BackgroundTasks, db: Session = Depends(get_db)):
    if not input.consent:
        raise HTTPException(status_code=400, detail="Consent is required")

    pid = new_id("u")
    prof = Profile(
        id=pid,
        linkedin_url=input.linkedin_url,
        resume_file_id=input.resume_file_id,
        resume_file_name=input.resume_file_name,
        topics_json=list_to_json(input.topics),
        interests_json=list_to_json(input.topics),
        available_now=input.available_now,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        source="resume" if input.resume_file_id else ("linkedin" if input.linkedin_url else None),
        hackathon=input.hackathon,
    )
    db.add(prof)
    db.commit()

    background.add_task(pipeline_run, db, pid)
    return ProfileWithStatus(profile=to_model(prof), status=prof.status)


@router.get("/{profile_id}", response_model=ProfileWithStatus)
async def get_profile(profile_id: str, db: Session = Depends(get_db)):
    p = db.get(Profile, profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileWithStatus(profile=to_model(p), status=p.status)


@router.patch("/{profile_id}")
async def patch_profile(profile_id: str, patch: PatchProfileInput, background: BackgroundTasks, db: Session = Depends(get_db)):
    p = db.get(Profile, profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")

    changed = False
    for field in ["name", "headline", "linkedin_url", "resume_file_id", "resume_file_name", "hackathon"]:
        val = getattr(patch, field)
        if val is not None:
            setattr(p, field, val)
            changed = True

    if patch.topics is not None:
        p.topics_json = list_to_json(patch.topics)
        changed = True
    if patch.skills_norm is not None:
        p.skills_norm_json = list_to_json(patch.skills_norm)
        changed = True
    if patch.interests is not None:
        p.interests_json = list_to_json(patch.interests)
        changed = True
    if patch.available_now is not None:
        p.available_now = patch.available_now
        changed = True

    if changed:
        p.updated_at = datetime.utcnow()
        db.add(p)
        db.commit()

    # If resume updated or explicit reembed endpoint used, pipeline will run; here we trigger if resume_file_id changed
    if patch.resume_file_id is not None:
        p.status = "pending"
        db.add(p)
        db.commit()
        background.add_task(pipeline_run, db, profile_id)

    return {"profile": to_model(p)}


@router.post("/{profile_id}/reembed")
async def reembed(profile_id: str, background: BackgroundTasks, db: Session = Depends(get_db)):
    p = db.get(Profile, profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    p.status = "pending"
    p.updated_at = datetime.utcnow()
    db.add(p)
    db.commit()
    background.add_task(pipeline_run, db, profile_id)
    return {"started": True}


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    p = db.get(Profile, profile_id)
    if not p:
        return {"ok": True}

    # delete from chroma
    delete_profile_index(profile_id)

    # delete upload file if present
    if p.resume_file_id:
        up = db.get(Upload, p.resume_file_id)
        if up and up.path and os.path.exists(up.path):
            try:
                os.remove(up.path)
            except Exception:
                pass
        if up:
            db.delete(up)

    db.delete(p)
    db.commit()
    return {"ok": True}
