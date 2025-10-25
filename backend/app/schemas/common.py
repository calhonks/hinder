from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class UploadPDFResponse(BaseModel):
    file_id: str
    file_name: str


class ParseStatusResponse(BaseModel):
    status: str


class ApiOK(BaseModel):
    ok: bool = True
