from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlmodel import Session
import os
from ..config import UPLOAD_DIR, ALLOWED_PDF_MB
from ..schemas.common import UploadPDFResponse
from ..db.models import Upload
from ..deps import get_db
from ..utils.ids import new_id

router = APIRouter(prefix="/files", tags=["files"]) 

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=UploadPDFResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
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

    upload = Upload(file_id=file_id, path=path, mime="application/pdf", size=len(content))
    db.add(upload)
    db.commit()

    return UploadPDFResponse(file_id=file_id, file_name=filename)
