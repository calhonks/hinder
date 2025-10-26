from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from sqlmodel import Session
import os
import hashlib
from typing import Optional
from ..config import UPLOAD_DIR, ALLOWED_PDF_MB
from ..schemas.common import UploadPDFResponse
from ..db.models import Upload, User
from ..deps import get_db
from ..utils.ids import new_id
from ..services.auth import decode_token

router = APIRouter(prefix="/uploads", tags=["uploads"]) 

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=UploadPDFResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    # Require auth and resolve current user
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = data.get("sub")
    try:
        current_user = db.get(User, int(uid))
    except Exception:
        current_user = None
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > ALLOWED_PDF_MB:
        raise HTTPException(status_code=400, detail=f"File too large; max {ALLOWED_PDF_MB}MB")

    file_id = new_id("file")
    filename = f"{file_id}.pdf"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    upload = Upload(file_id=file_id, user_id=current_user.id, path=path, mime="application/pdf", size=len(content))
    db.add(upload)
    db.commit()

    return UploadPDFResponse(file_id=file_id, file_name=filename)
