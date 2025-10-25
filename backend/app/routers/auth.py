from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlmodel import Session, select
from typing import Optional
from ..deps import get_db
from ..db.models import User
from ..services.auth import hash_password, verify_password, create_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"]) 


@router.post("/signup")
async def signup(payload: dict, db: Session = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="name, email, and password are required")

    exists = db.exec(select(User).where(User.email == email)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(str(user.id))
    return {"token": token, "user": {"id": str(user.id), "name": user.name, "email": user.email}}


@router.post("/login")
async def login(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(str(user.id))
    return {"token": token, "user": {"id": str(user.id), "name": user.name, "email": user.email}}


def _get_current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> Optional[User]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    data = decode_token(token)
    if not data:
        return None
    uid = data.get("sub")
    try:
        return db.get(User, int(uid))
    except Exception:
        return None


@router.get("/me")
async def me(user: Optional[User] = Depends(_get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"id": str(user.id), "name": user.name, "email": user.email}
