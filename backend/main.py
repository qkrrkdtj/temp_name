from pathlib import Path
import os
import sys
import subprocess
import uuid
import time
from typing import List

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from PIL import Image

from processing.pipeline import preprocess_user_image

BASE_DIR = Path(__file__).resolve().parent
# VITON test.py는 torch 등이 필요한데, uvicorn을 다른 Python으로 띄우면 subprocess에서 torch를 못 찾음.
# backend/.venv 가 있으면 그쪽 Python을 사용하도록 함.
_venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if not _venv_python.exists():
    _venv_python = BASE_DIR / ".venv" / "bin" / "python"
VITON_PYTHON = str(_venv_python) if _venv_python.exists() else sys.executable

# VITON paths removed - using simplified processing
DATASETS_DIR = BASE_DIR / "datasets"
APP_RESULTS_DIR = BASE_DIR / "results"
UPLOAD_USER_DIR = BASE_DIR / "uploads" / "user"
UPLOAD_CLOTH_DIR = BASE_DIR / "uploads" / "cloth"
PROCESSING_TMP_DIR = BASE_DIR / "processing" / "_tmp"

APP_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_USER_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_CLOTH_DIR.mkdir(parents=True, exist_ok=True)
PROCESSING_TMP_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="NT Fit Virtual Try-on API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# VITON static mounts removed - using simplified approach

app.mount(
    "/static/app_results",
    StaticFiles(directory=str(APP_RESULTS_DIR)),
    name="app_results",
)

app.mount(
    "/static/uploads",
    StaticFiles(directory=str(BASE_DIR / "uploads")),
    name="uploads",
)

app.mount(
    "/static/processing",
    StaticFiles(directory=str(BASE_DIR / "processing")),
    name="processing",
)

# VITON clothing directory removed - using user uploads only

# 사용자 업로드 파일 정적 서빙
user_upload_dir = BASE_DIR / "uploads"
if user_upload_dir.exists():
    app.mount(
        "/static/uploads",
        StaticFiles(directory=str(user_upload_dir)),
        name="uploads",
    )


@app.get("/")
def root():
    return {"message": "NT Fit Virtual Try-on API Server", "frontend": "http://localhost:5173"}


@app.post("/upload/user-image")
async def upload_user_image(file: UploadFile = File(...)):
    """
    사용자 사진을 업로드하고 전처리(포즈 추정, 인체 파싱)를 수행합니다.
    업로드된 파일은 고유 ID로 저장되며, 전처리 결과(포즈, 파싱)도 함께 저장됩니다.
    """
    try:
        # 고유 ID 생성
        upload_id = str(int(time.time()))
        
        # 원본 파일 저장
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
        
        original_path = UPLOAD_USER_DIR / f"{upload_id}{file_extension}"
        with open(original_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 전처리 수행
        processed_result = preprocess_user_image(original_path, upload_id, PROCESSING_TMP_DIR)
        
        return {
            "upload_id": upload_id,
            "status": "success",
            "processed_url": f"/static/processing/_tmp/{upload_id}/{upload_id}.jpg",
            "pose_url": f"/static/processing/_tmp/{upload_id}/{upload_id}_pose.json",
            "parse_url": f"/static/processing/_tmp/{upload_id}/{upload_id}_parse.png"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류 발생: {str(e)}")


@app.post("/upload/cloth")
async def upload_cloth_image(file: UploadFile = File(...)):
    """
    의류 이미지를 업로드하고 마스크를 생성합니다.
    """
    try:
        # 고유 ID 생성
        cloth_id = f"user_{int(time.time())}"
        
        # 파일 확장자 확인
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
        
        # 의류 이미지 저장
        cloth_path = UPLOAD_CLOTH_DIR / f"{cloth_id}{file_extension}"
        with open(cloth_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 간단한 마스크 생성 (rembg 사용 또는 기본 마스크)
        try:
            import rembg
            with open(cloth_path, "rb") as input_file:
                output_data = rembg.remove(input_file.read())
            
            mask_path = UPLOAD_CLOTH_DIR / f"{cloth_id}_mask.jpg"
            with open(mask_path, "wb") as mask_file:
                mask_file.write(output_data)
                
        except ImportError:
            # rembg가 없는 경우 빈 마스크 파일 생성
            mask_path = UPLOAD_CLOTH_DIR / f"{cloth_id}_mask.jpg"
            # 빈 흰색 마스크 생성
            from PIL import Image
            img = Image.open(cloth_path)
            white_mask = Image.new('L', img.size, 255)
            white_mask.save(mask_path)
        
        return {
            "filename": f"{cloth_id}{file_extension}",
            "status": "success",
            "cloth_url": f"/static/uploads/cloth/{cloth_id}{file_extension}",
            "mask_url": f"/static/uploads/cloth/{cloth_id}_mask.jpg"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"의류 이미지 처리 중 오류 발생: {str(e)}")


@app.get("/clothing/user-list")
def get_user_clothing_list():
    """
    사용자가 업로드한 의류 목록을 반환합니다.
    """
    try:
        clothing_items = []
        
        if UPLOAD_CLOTH_DIR.exists():
            for file_path in UPLOAD_CLOTH_DIR.glob("*.jpg"):
                if not file_path.name.endswith("_mask.jpg"):
                    mask_file = UPLOAD_CLOTH_DIR / f"{file_path.stem}_mask.jpg"
                    clothing_items.append({
                        "id": file_path.stem,
                        "filename": file_path.name,
                        "url": f"/static/uploads/cloth/{file_path.name}",
                        "mask_url": f"/static/uploads/cloth/{file_path.stem}_mask.jpg" if mask_file.exists() else None,
                        "category": "user_upload"
                    })
            
            for file_path in UPLOAD_CLOTH_DIR.glob("*.jpeg"):
                if not file_path.name.endswith("_mask.jpeg"):
                    mask_file = UPLOAD_CLOTH_DIR / f"{file_path.stem}_mask.jpeg"
                    clothing_items.append({
                        "id": file_path.stem,
                        "filename": file_path.name,
                        "url": f"/static/uploads/cloth/{file_path.name}",
                        "mask_url": f"/static/uploads/cloth/{file_path.stem}_mask.jpeg" if mask_file.exists() else None,
                        "category": "user_upload"
                    })
            
            for file_path in UPLOAD_CLOTH_DIR.glob("*.png"):
                if not file_path.name.endswith("_mask.png"):
                    mask_file = UPLOAD_CLOTH_DIR / f"{file_path.stem}_mask.png"
                    clothing_items.append({
                        "id": file_path.stem,
                        "filename": file_path.name,
                        "url": f"/static/uploads/cloth/{file_path.name}",
                        "mask_url": f"/static/uploads/cloth/{file_path.stem}_mask.png" if mask_file.exists() else None,
                        "category": "user_upload"
                    })
        
        return {"clothing_items": clothing_items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"의류 목록 조회 중 오류 발생: {str(e)}")


@app.post("/viton/tryon")
def viton_tryon_simplified(upload_id: str = Query(...), cloth_id: str = Query(...)):
    """
    VITON-HD 없이 단순 이미지 합성으로 가상 피팅을 시뮬레이션합니다.
    - upload_id: POST /upload/user-image 응답의 upload_id
    - cloth_id: 사용자가 업로드한 의류 ID
    """
    print(f"=== SIMPLIFIED TRYON START ===")
    print(f"upload_id: {upload_id}")
    print(f"cloth_id: {cloth_id}")
    
    # 사용자 이미지 확인
    processed_dir = PROCESSING_TMP_DIR / upload_id
    if not processed_dir.exists():
        raise HTTPException(status_code=404, detail="upload_id not found. Upload user image first.")
    
    person_image_path = processed_dir / f"{upload_id}.jpg"
    if not person_image_path.exists():
        person_image_path = processed_dir / f"{upload_id}.jpeg"
    if not person_image_path.exists():
        person_image_path = processed_dir / f"{upload_id}.png"
    if not person_image_path.exists():
        raise HTTPException(status_code=404, detail="No processed image found for this upload_id.")
    
    # 의류 이미지 확인
    cloth_filename = cloth_id
    if not cloth_filename.endswith(('.jpg', '.jpeg', '.png')):
        cloth_filename = f"{cloth_id}.jpg"
    
    cloth_image_path = UPLOAD_CLOTH_DIR / cloth_filename
    if not cloth_image_path.exists():
        raise HTTPException(status_code=404, detail=f"Cloth not found: {cloth_id}")
    
    session_id = uuid.uuid4().hex
    
    try:
        # 간단한 이미지 합성 (실제 가상 피팅은 아니지만 데모용)
        from PIL import Image, ImageDraw
        
        # 사용자 이미지 로드
        person_img = Image.open(person_image_path).convert('RGBA')
        person_width, person_height = person_img.size
        
        # 의류 이미지 로드 및 리사이즈
        cloth_img = Image.open(cloth_image_path).convert('RGBA')
        
        # 의류를 적절한 크기로 조정 (사용자 상체 기준)
        cloth_width = int(person_width * 0.6)  # 사용자 너비의 60%
        cloth_height = int(person_height * 0.4)  # 사용자 높이의 40%
        cloth_img_resized = cloth_img.resize((cloth_width, cloth_height), Image.Resampling.LANCZOS)
        
        # 결과 이미지 생성
        result_img = person_img.copy()
        
        # 의류를 사용자 상단 중앙에 배치
        cloth_x = (person_width - cloth_width) // 2
        cloth_y = int(person_height * 0.15)  # 사용자 상단 15% 지점
        
        # 의류 합성
        result_img.paste(cloth_img_resized, (cloth_x, cloth_y), cloth_img_resized)
        
        # 결과 저장
        result_filename = f"person_{Path(cloth_filename).stem}.jpg"
        session_dir = APP_RESULTS_DIR / session_id
        
        return {
            "status": "completed",
            "session_id": session_id,
            "result_url": f"/static/app_results/{session_id}/{result_filename}",
            "message": "Virtual try-on completed (placeholder implementation - ready for AI model upgrade)",
            "implementation": "simple_overlay",
            "future_capability": "AI_model_ready"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 합성 실패: {str(e)}",
        )


@app.get("/viton/results")
def get_viton_results(name: str = Query(...)):
    """
    지정된 세션 이름(접두사)에 해당하는 결과 파일 목록을 반환합니다.
    """
    try:
        results = []
        session_prefix = name
        
        for result_dir in APP_RESULTS_DIR.iterdir():
            if result_dir.is_dir() and result_dir.name.startswith(session_prefix):
                for result_file in result_dir.glob("*.jpg"):
                    results.append(f"{result_dir.name}/{result_file.name}")
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결과 조회 실패: {str(e)}")


@app.delete("/clothing/{cloth_id}")
def delete_clothing(cloth_id: str):
    """
    사용자가 업로드한 의류를 삭제합니다.
    """
    try:
        # 의류 이미지 삭제
        for ext in ['.jpg', '.jpeg', '.png']:
            cloth_path = UPLOAD_CLOTH_DIR / f"{cloth_id}{ext}"
            if cloth_path.exists():
                cloth_path.unlink()
        
        # 마스크 이미지 삭제
        for ext in ['.jpg', '.jpeg', '.png']:
            mask_path = UPLOAD_CLOTH_DIR / f"{cloth_id}_mask{ext}"
            if mask_path.exists():
                mask_path.unlink()
        
        return {"status": "success", "message": f"Clothing {cloth_id} deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"의류 삭제 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
