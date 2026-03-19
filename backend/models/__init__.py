from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    status: str
    upload_id: Optional[str] = None
    filename: Optional[str] = None
    message: Optional[str] = None

class VitonRequest(BaseModel):
    upload_id: str
    cloth_id: str

class VitonResponse(BaseModel):
    status: str
    session_id: str
    result_url: str
    result_filename: str
