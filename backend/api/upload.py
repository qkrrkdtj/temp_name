from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List
import uuid
import time

from ..models import UploadResponse
from ..services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["upload"])

upload_service = UploadService()

@router.post("/user-image", response_model=UploadResponse)
async def upload_user_image(file: UploadFile = File(...)):
    """사용자 이미지를 업로드하고 전처리합니다."""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")
    
    try:
        upload_id = await upload_service.process_user_image(file)
        return UploadResponse(status="success", upload_id=upload_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 전처리 실패: {e}")

@router.post("/cloth", response_model=UploadResponse)
async def upload_cloth(file: UploadFile = File(...)):
    """옷 이미지를 업로드합니다."""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")
    
    try:
        filename = await upload_service.save_cloth_image(file)
        return UploadResponse(status="success", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"옷 업로드 실패: {e}")

@router.get("/user-clothes", response_model=List[str])
def get_user_clothes():
    """사용자가 업로드한 옷 목록을 반환합니다."""
    try:
        return upload_service.get_user_clothes_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 옷 목록 조회 실패: {e}")

@router.delete("/cloth/{filename}")
def delete_user_cloth(filename: str):
    """사용자가 업로드한 옷을 삭제합니다."""
    try:
        success = upload_service.delete_user_cloth(filename)
        if not success:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        return {"status": "success", "message": "파일이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {e}")
