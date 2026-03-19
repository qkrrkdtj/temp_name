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
from processing.viton_preprocess import build_viton_input_dir, generate_cloth_mask, VITON_SIZE

BASE_DIR = Path(__file__).resolve().parent
# VITON test.py는 torch 등이 필요한데, uvicorn을 다른 Python으로 띄우면 subprocess에서 torch를 못 찾음.
# backend/.venv 가 있으면 그쪽 Python을 사용하도록 함.
_venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if not _venv_python.exists():
    _venv_python = BASE_DIR / ".venv" / "bin" / "python"
VITON_PYTHON = str(_venv_python) if _venv_python.exists() else sys.executable

VITON_ROOT = BASE_DIR / "viton_hd"
DATASETS_DIR = VITON_ROOT / "datasets"
CHECKPOINTS_DIR = VITON_ROOT / "checkpoints"
RESULTS_DIR = VITON_ROOT / "results"
APP_RESULTS_DIR = BASE_DIR / "results"
CLOTHING_ONLY_DIR = DATASETS_DIR / "clothing_only"
TEST_CLOTH_DIR = DATASETS_DIR / "test" / "cloth"
TEST_CLOTH_MASK_DIR = DATASETS_DIR / "test" / "cloth-mask"
UPLOAD_USER_DIR = BASE_DIR / "uploads" / "user"
PROCESSING_TMP_DIR = BASE_DIR / "processing" / "_tmp"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
APP_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_USER_DIR.mkdir(parents=True, exist_ok=True)
PROCESSING_TMP_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="test_FIT VITON-HD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static/results",
    StaticFiles(directory=str(RESULTS_DIR)),
    name="results",
)

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

if CLOTHING_ONLY_DIR.exists():
    app.mount(
        "/static/clothing_only",
        StaticFiles(directory=str(CLOTHING_ONLY_DIR)),
        name="clothing_only",
    )

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
    return {"message": "NT Fit VITON-HD API Server", "frontend": "http://localhost:5173"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/viton/run")
def viton_run(name: str = "web_demo"):
    """
    미리 준비된 test 데이터셋과 체크포인트를 이용해
    VITON-HD 추론을 한 번 실행합니다.
    """
    test_py = VITON_ROOT / "test.py"
    if not test_py.exists():
        raise HTTPException(status_code=404, detail="viton_hd/test.py not found")

    cmd = [
        VITON_PYTHON,
        str(test_py),
        "--name",
        name,
        "--dataset_dir",
        str(DATASETS_DIR),
        "--checkpoint_dir",
        str(CHECKPOINTS_DIR),
        "--save_dir",
        str(RESULTS_DIR),
    ]
    subprocess.run(cmd, check=True, cwd=str(VITON_ROOT))
    return {"status": "completed", "name": name}


@app.post("/viton/tryon")
def viton_tryon(upload_id: str = Query(...), cloth_id: str = Query(...)):
    """
    업로드된 사용자 이미지(upload_id)와 선택한 의류(cloth_id)로
    가상 피팅을 수행합니다. 전처리(포즈/파싱) → VITON-HD 파이프라인을 거쳐
    결과 이미지를 생성하고 세션 ID와 URL을 반환합니다.
    - upload_id: POST /upload/user-image 응답의 upload_id
    - cloth_id: 예) "001/1116155.jpg" 또는 "user_1234567890.jpg"
    """
    print(f"=== VITON TRYON START ===")
    print(f"upload_id: {upload_id}")
    print(f"cloth_id: {cloth_id}")
    
    # 사용자 이미지: 전처리 시 저장한 파일만 사용 (폴더 내 다른 파일에 의존하지 않음)
    # pipeline은 항상 {upload_id}.jpg 로 저장함 (input_path.stem == upload_id)
    processed_dir = PROCESSING_TMP_DIR / upload_id
    print(f"processed_dir: {processed_dir}")
    print(f"processed_dir.exists(): {processed_dir.exists()}")
    
    if not processed_dir.exists():
        print(f"ERROR: upload_id not found. Upload user image first.")
        raise HTTPException(status_code=404, detail="upload_id not found. Upload user image first.")
    
    person_image_path = processed_dir / f"{upload_id}.jpg"
    if not person_image_path.exists():
        person_image_path = processed_dir / f"{upload_id}.jpeg"
    if not person_image_path.exists():
        person_image_path = processed_dir / f"{upload_id}.png"
    if not person_image_path.exists():
        print(f"ERROR: No processed image found for this upload_id.")
        raise HTTPException(status_code=404, detail="No processed image found for this upload_id.")
    
    print(f"person_image_path: {person_image_path}")
    print(f"person_image_path.exists(): {person_image_path.exists()}")

    # 의류: cloth_id로 지정한 파일만 사용 (폴더 내 다른 파일/순서에 의존하지 않음)
    cloth_safe = cloth_id.replace("\\", "/").strip().lstrip("/")
    cloth_filename = cloth_safe.replace("/", "_")
    cloth_image_path = None
    cloth_mask_path = None
    
    # 1. 사용자 업로드 옷 확인
    user_cloth_dir = BASE_DIR / "uploads" / "cloth"
    
    # cloth_id에 확장자가 있는지 확인
    if cloth_id.endswith('.jpg') or cloth_id.endswith('.jpeg') or cloth_id.endswith('.png'):
        user_cloth_path = user_cloth_dir / cloth_id
        user_mask_path = user_cloth_dir / f"{cloth_id.rsplit('.', 1)[0]}_mask.jpg"
        cloth_filename = cloth_id
    else:
        user_cloth_path = user_cloth_dir / f"{cloth_id}.jpg"
        user_mask_path = user_cloth_dir / f"{cloth_id}_mask.jpg"
        cloth_filename = f"{cloth_id}.jpg"
    
    print(f"user_cloth_path: {user_cloth_path}")
    print(f"user_cloth_path.exists(): {user_cloth_path.exists()}")
    
    if user_cloth_path.exists():
        cloth_image_path = user_cloth_path
        if user_mask_path.exists():
            cloth_mask_path = user_mask_path
    # 2. 기존 카테고리 옷 확인
    elif CLOTHING_ONLY_DIR.exists():
        candidate = CLOTHING_ONLY_DIR / cloth_safe
        if candidate.exists() and candidate.is_file():
            cloth_image_path = candidate
    # 3. 테스트 옷 확인
    if cloth_image_path is None:
        candidate = TEST_CLOTH_DIR / cloth_filename
        if candidate.exists() and candidate.is_file():
            cloth_image_path = candidate
    
    if cloth_image_path is None:
        raise HTTPException(status_code=404, detail=f"Cloth not found: {cloth_id}")

    # 마스크 경로 확인 (사용자 옷이 아닌 경우)
    if cloth_mask_path is None and TEST_CLOTH_MASK_DIR.exists():
        mask_candidate = TEST_CLOTH_MASK_DIR / cloth_filename
        if mask_candidate.exists():
            cloth_mask_path = mask_candidate
    if cloth_mask_path is None and (DATASETS_DIR / "cloth_mask").exists():
        mask_candidate = DATASETS_DIR / "cloth_mask" / cloth_filename
        if mask_candidate.exists():
            cloth_mask_path = mask_candidate

    session_id = uuid.uuid4().hex
    try:
        viton_test_dir = build_viton_input_dir(
            person_image_path=person_image_path,
            cloth_image_path=cloth_image_path,
            cloth_mask_path=cloth_mask_path,
            session_id=session_id,
            out_base_dir=PROCESSING_TMP_DIR,
            person_filename="person.jpg",
            cloth_filename=cloth_filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"전처리 실패 (포즈/파싱/의류 마스크): {e!s}",
        )

    # VITON 입력 파일 존재 여부 확인
    test_dir = viton_test_dir / "test"
    required = [
        test_dir / "image" / "person.jpg",
        test_dir / "cloth" / cloth_filename,
        test_dir / "cloth-mask" / cloth_filename,
        test_dir / "image-parse" / "person.png",
        test_dir / "openpose-json" / "person_keypoints.json",
        viton_test_dir / "test_pairs.txt",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"VITON 입력 파일 누락: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
        )

    test_py = VITON_ROOT / "test.py"
    if not test_py.exists():
        raise HTTPException(status_code=404, detail="viton_hd/test.py not found")

    # 절대 경로 사용으로 cwd/상대경로 이슈 방지
    dataset_dir_abs = str(viton_test_dir.resolve())
    checkpoint_dir_abs = str(CHECKPOINTS_DIR.resolve())
    save_dir_abs = str(APP_RESULTS_DIR.resolve())
    # --workers 0: 단일 쌍 tryon 시 워커 프로세스에서 경로 오류(FileNotFoundError) 방지
    cmd = [
        VITON_PYTHON,
        str(test_py),
        "--name",
        session_id,
        "--dataset_dir",
        dataset_dir_abs,
        "--dataset_mode",
        "test",
        "--checkpoint_dir",
        checkpoint_dir_abs,
        "--save_dir",
        save_dir_abs,
        "--workers",
        "0",
    ]
    import logging
    log = logging.getLogger("viton")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(VITON_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="VITON run timed out (300s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VITON subprocess error: {e!s}")

    if result.returncode != 0:
        err_msg = (result.stderr or "").strip() or (result.stdout or "").strip()
        if not err_msg:
            err_msg = f"exit code {result.returncode}"
        log.error("VITON stderr: %s", result.stderr)
        log.error("VITON stdout: %s", result.stdout)
        raise HTTPException(status_code=500, detail=f"VITON run failed: {err_msg[:2000]}")

    # 결과 파일명: test.py save_images 규칙에 따라 "person_{cloth_stem}.jpg" 고정
    result_filename = f"person_{Path(cloth_filename).stem}.jpg"
    result_path = APP_RESULTS_DIR / session_id / result_filename
    if not result_path.exists():
        # 생성된 파일이 다른 이름일 수 있으면 한 개만 찾아서 반환
        out_dir = APP_RESULTS_DIR / session_id
        if out_dir.exists():
            first_jpg = next(out_dir.glob("*.jpg"), None)
            if first_jpg is not None:
                result_filename = first_jpg.name
    result_url = f"/static/app_results/{session_id}/{result_filename}"

    return {
        "status": "completed",
        "session_id": session_id,
        "result_url": result_url,
        "result_filename": result_filename,
    }


@app.get("/viton/results")
def viton_results(name: str = "web_demo") -> List[str]:
    """
    생성된 결과 이미지 파일 리스트를 반환합니다.
    (프론트엔드에서 갤러리처럼 표시 가능)
    """
    target_dir = APP_RESULTS_DIR / name
    if not target_dir.exists():
        return []

    images = [
        f.name
        for f in sorted(target_dir.glob("*.jpg"))
    ]
    return images


@app.post("/upload/user-image")
async def upload_user_image(file: UploadFile = File(...)):
    """
    웹에서 업로드한 사용자 이미지를 backend/uploads/user 에 저장합니다.
    저장 후 전처리 결과(리사이즈/포맷)를 backend/processing/_tmp 에 함께 생성합니다.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    ext = (Path(file.filename).suffix or ".jpg").lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="unsupported file type")

    upload_id = uuid.uuid4().hex
    raw_path = UPLOAD_USER_DIR / f"{upload_id}{ext}"

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    raw_path.write_bytes(content)

    pre = preprocess_user_image(
        input_path=raw_path,
        out_dir=PROCESSING_TMP_DIR / upload_id,
        max_size=1024,
        out_format="jpg",
    )

    return {
        "upload_id": upload_id,
        "raw_path": str(raw_path),
        "processed_path": str(pre.processed_path),
        "processed_size": {"width": pre.size[0], "height": pre.size[1]},
        "raw_url": f"/static/uploads/user/{raw_path.name}",
        "processed_url": f"/static/processing/_tmp/{upload_id}/{pre.processed_path.name}",
    }


@app.post("/upload/cloth-image")
async def upload_cloth_image(file: UploadFile = File(...)):
    """
    사용자가 직접 옷 이미지를 업로드하는 기능입니다.
    업로드된 옷 이미지는 VITON 처리를 위해 적절한 형태로 전처리됩니다.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    ext = (Path(file.filename).suffix or ".jpg").lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="unsupported file type")

    cloth_id = uuid.uuid4().hex
    user_cloth_dir = BASE_DIR / "uploads" / "cloth"
    user_cloth_dir.mkdir(parents=True, exist_ok=True)
    
    raw_path = user_cloth_dir / f"{cloth_id}{ext}"
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    raw_path.write_bytes(content)
    
    # 옷 이미지 전처리 (VITON 해상도로 리사이즈)
    try:
        processed_path = user_cloth_dir / f"{cloth_id}.jpg"
        with Image.open(raw_path) as img:
            img = img.convert("RGB")
            img = img.resize((VITON_SIZE[0], VITON_SIZE[1]), Image.Resampling.LANCZOS)
            img.save(processed_path, quality=95)
            
        # 옷 마스크 생성 (실패해도 계속 진행)
        mask_path = user_cloth_dir / f"{cloth_id}_mask.jpg"
        try:
            generate_cloth_mask(processed_path, mask_path)
        except Exception as mask_error:
            print(f"Warning: Mask generation failed: {mask_error}")
            # 마스크 생성 실패해도 빈 파일 생성
            mask_path.touch()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloth preprocessing failed: {e!s}")

    return {
        "cloth_id": cloth_id,
        "raw_path": str(raw_path),
        "processed_path": str(processed_path),
        "mask_path": str(mask_path) if mask_path.exists() else None,
        "raw_url": f"/static/uploads/cloth/{raw_path.name}",
        "processed_url": f"/static/uploads/cloth/{processed_path.name}",
        "mask_url": f"/static/uploads/cloth/{mask_path.name}" if mask_path.exists() else None,
    }


@app.get("/clothing/user-list")
def get_user_cloth_list() -> List[dict]:
    """
    사용자가 업로드한 옷 이미지 목록을 반환합니다.
    """
    user_cloth_dir = BASE_DIR / "uploads" / "cloth"
    if not user_cloth_dir.exists():
        return []
    
    cloth_list = []
    for file_path in user_cloth_dir.glob("*.jpg"):
        if "_mask" not in file_path.name:
            cloth_id = file_path.stem
            mask_path = user_cloth_dir / f"{cloth_id}_mask.jpg"
            cloth_list.append({
                "cloth_id": cloth_id,
                "filename": file_path.name,
                "processed_url": f"/static/uploads/cloth/{file_path.name}",
                "mask_url": f"/static/uploads/cloth/{mask_path.name}" if mask_path.exists() else None,
            })
    
    return sorted(cloth_list, key=lambda x: x["cloth_id"], reverse=True)


@app.delete("/clothing/user/{cloth_id}")
def delete_user_cloth(cloth_id: str):
    """
    사용자가 업로드한 특정 옷 이미지를 삭제합니다.
    """
    user_cloth_dir = BASE_DIR / "uploads" / "cloth"
    
    # 삭제할 파일들
    files_to_delete = [
        user_cloth_dir / f"{cloth_id}.jpg",
        user_cloth_dir / f"{cloth_id}_mask.jpg",
        user_cloth_dir / f"{cloth_id}.png",  # 다른 확장자도 고려
        user_cloth_dir / f"{cloth_id}_mask.png",
        user_cloth_dir / f"{cloth_id}.jpeg",
        user_cloth_dir / f"{cloth_id}_mask.jpeg",
        user_cloth_dir / f"{cloth_id}.webp",
        user_cloth_dir / f"{cloth_id}_mask.webp",
    ]
    
    deleted_files = []
    for file_path in files_to_delete:
        if file_path.exists():
            file_path.unlink()
            deleted_files.append(file_path.name)
    
    if not deleted_files:
        raise HTTPException(status_code=404, detail="Cloth not found")
    
    return {"message": f"Deleted {len(deleted_files)} files", "files": deleted_files}


@app.get("/clothing/categories")
def clothing_categories() -> List[str]:
    """
    clothing_only 아래의 카테고리(폴더) 목록을 반환합니다.
    예) ["001", "002"]
    """
    if not CLOTHING_ONLY_DIR.exists():
        return []
    return [p.name for p in sorted(CLOTHING_ONLY_DIR.iterdir()) if p.is_dir()]


@app.get("/clothing/list")
def clothing_list(category: str, limit: int = 200) -> List[str]:
    """
    선택한 카테고리(폴더) 안의 이미지 파일 목록을 반환합니다.
    반환 형식은 "001/xxxx.jpg" 처럼 정적 경로와 바로 연결 가능한 상대경로입니다.
    """
    if not CLOTHING_ONLY_DIR.exists():
        return []

    cat_dir = CLOTHING_ONLY_DIR / category
    if not cat_dir.exists() or not cat_dir.is_dir():
        raise HTTPException(status_code=404, detail="category not found")

    limit = max(1, min(int(limit), 2000))
    files: List[str] = []
    for f in sorted(cat_dir.glob("*.jpg")):
        files.append(f"{category}/{f.name}")
        if len(files) >= limit:
            break
    return files


@app.post("/upload/user-image")
async def upload_user_image(file: UploadFile = File(...)):
    """
    사용자 이미지를 업로드하고 전처리합니다.
    반환된 upload_id는 /viton/tryon에서 사용됩니다.
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")
    
    # 고유 ID 생성
    upload_id = uuid.uuid4().hex[:12]  # 12자리 ID
    
    try:
        # 파일 내용 읽기
        contents = await file.read()
        
        # 임시 파일로 저장
        temp_file = PROCESSING_TMP_DIR / f"{upload_id}_temp.jpg"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_file, "wb") as f:
            f.write(contents)
        
        # 전처리 실행
        processed_dir = PROCESSING_TMP_DIR / upload_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        preprocess_user_image(
            input_path=temp_file,
            output_dir=processed_dir,
            person_filename=f"{upload_id}.jpg"
        )
        
        # 임시 파일 삭제
        temp_file.unlink()
        
        return {"upload_id": upload_id, "status": "success"}
        
    except Exception as e:
        # 오류 시 임시 파일 정리
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=500, detail=f"이미지 전처리 실패: {e!s}")


@app.post("/upload/cloth")
async def upload_cloth(file: UploadFile = File(...)):
    """
    옷 이미지를 업로드합니다.
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")
    
    try:
        # 파일 내용 읽기
        contents = await file.read()
        
        # 고유 파일명 생성
        timestamp = int(time.time())
        filename = f"user_{timestamp}.jpg"
        
        # 저장
        cloth_dir = BASE_DIR / "uploads" / "cloth"
        cloth_dir.mkdir(parents=True, exist_ok=True)
        
        cloth_path = cloth_dir / filename
        with open(cloth_path, "wb") as f:
            f.write(contents)
        
        return {"filename": filename, "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"옷 업로드 실패: {e!s}")


@app.delete("/uploads/cloth/{filename}")
def delete_user_cloth(filename: str):
    """
    사용자가 업로드한 옷을 삭제합니다.
    """
    try:
        cloth_dir = BASE_DIR / "uploads" / "cloth"
        cloth_path = cloth_dir / filename
        
        if not cloth_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        cloth_path.unlink()
        return {"status": "success", "message": "파일이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {e!s}")


@app.get("/uploads/user-clothes")
def get_user_clothes():
    """
    사용자가 업로드한 옷 목록을 반환합니다.
    """
    try:
        cloth_dir = BASE_DIR / "uploads" / "cloth"
        if not cloth_dir.exists():
            return []
        
        clothes = []
        for file_path in cloth_dir.glob("*.jpg"):
            clothes.append(file_path.name)
        
        # 최신순으로 정렬
        clothes.sort(reverse=True)
        return clothes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 옷 목록 조회 실패: {e!s}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

