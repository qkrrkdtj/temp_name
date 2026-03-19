from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import traceback
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# 프로젝트 기본 경로
# backend/main.py 기준
# ==============================
BASE_DIR = Path(__file__).resolve().parent          # .../backend
PROJECT_ROOT = BASE_DIR.parent                      # .../project root

# ==============================
# 서버 기본 경로
# ==============================
PERSON_DIR = BASE_DIR / "uploads" / "person"
CLOTH_DIR = BASE_DIR / "uploads" / "cloth"

# ==============================
# StableVITON 파이프라인 경로
# ==============================
PIPELINE_ROOT = PROJECT_ROOT / "StableVITON" / "pipeline"
PIPELINE_SCRIPT = PIPELINE_ROOT / "main_pipeline.py"

# 환경변수 우선, 없으면 현재 파이썬 사용
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", sys.executable)

PIPELINE_INPUT_PERSON_DIR = PIPELINE_ROOT / "input_drop" / "person"
PIPELINE_INPUT_CLOTH_DIR = PIPELINE_ROOT / "input_drop" / "cloth"

# ==============================
# 웹에 보여줄 옷 목록 폴더
# ==============================
CLOTHING_STATIC_DIR = PROJECT_ROOT / "StableVITON" / "data" / "custom" / "test" / "cloth"

# ==============================
# 결과 폴더
# ==============================
RUNS_DIR = PROJECT_ROOT / "StableVITON" / "runs"

PERSON_DIR.mkdir(parents=True, exist_ok=True)
CLOTH_DIR.mkdir(parents=True, exist_ok=True)
CLOTHING_STATIC_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_INPUT_PERSON_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_INPUT_CLOTH_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/static/cloth",
    StaticFiles(directory=str(CLOTHING_STATIC_DIR)),
    name="cloth"
)

app.mount(
    "/static/runs",
    StaticFiles(directory=str(RUNS_DIR)),
    name="static_runs"
)


def make_filename(prefix: str, original_name: str) -> str:
    ext = Path(original_name).suffix.lower()
    if not ext:
        ext = ".jpg"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}{ext}"


def list_clothing_files(limit: int = 200) -> list[str]:
    if not CLOTHING_STATIC_DIR.exists() or not CLOTHING_STATIC_DIR.is_dir():
        return []

    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    files = []

    for item in sorted(CLOTHING_STATIC_DIR.iterdir()):
        if item.is_file() and item.suffix.lower() in allowed_exts:
            files.append(item.name)

    return files[:limit]


def get_latest_job_dir(runs_dir: Path):
    job_dirs = [
        p for p in runs_dir.iterdir()
        if p.is_dir() and p.name.startswith("job_")
    ]
    if not job_dirs:
        return None

    job_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return job_dirs[0]


def find_result_image_in_job(job_dir: Path):
    results_dir = job_dir / "results"
    if not results_dir.exists():
        return None, None

    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    image_files = [
        p for p in results_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in allowed_exts
    ]

    if not image_files:
        return None, None

    image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    result_path = image_files[0]

    relative_path = result_path.relative_to(RUNS_DIR).as_posix()
    result_url = f"/static/runs/{relative_path}"

    return str(result_path), result_url


def clear_folder(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def copy_to_pipeline_input(person_src: Path, cloth_src: Path):
    clear_folder(PIPELINE_INPUT_PERSON_DIR)
    clear_folder(PIPELINE_INPUT_CLOTH_DIR)

    shutil.copy2(person_src, PIPELINE_INPUT_PERSON_DIR / "person.jpg")
    shutil.copy2(cloth_src, PIPELINE_INPUT_CLOTH_DIR / "cloth.jpg")


@app.get("/")
def root():
    return {
        "message": "server is running",
        "project_root": str(PROJECT_ROOT),
        "pipeline_script": str(PIPELINE_SCRIPT),
    }


@app.get("/clothing/debug")
def clothing_debug():
    if not CLOTHING_STATIC_DIR.exists():
        return {
            "exists": False,
            "path": str(CLOTHING_STATIC_DIR),
            "count": 0,
            "files": []
        }

    files = [
        f.name for f in sorted(CLOTHING_STATIC_DIR.iterdir())
        if f.is_file()
    ]

    return {
        "exists": True,
        "path": str(CLOTHING_STATIC_DIR),
        "count": len(files),
        "files": files[:50]
    }


@app.get("/clothing/list")
def get_clothing_list(
    limit: int = Query(1000, ge=1, le=5000)
):
    files = list_clothing_files(limit)
    return {
        "files": files,
        "count": len(files)
    }


@app.post("/upload")
def upload_images(
    person_image: UploadFile = File(...),
    cloth_image: UploadFile = File(...)
):
    person_filename = make_filename("person", person_image.filename)
    cloth_filename = make_filename("cloth", cloth_image.filename)

    person_path = PERSON_DIR / person_filename
    cloth_path = CLOTH_DIR / cloth_filename

    with person_path.open("wb") as buffer:
        shutil.copyfileobj(person_image.file, buffer)

    with cloth_path.open("wb") as buffer:
        shutil.copyfileobj(cloth_image.file, buffer)

    return {
        "message": "upload success",
        "person_image": str(person_path),
        "cloth_image": str(cloth_path),
        "person_filename": person_filename,
        "cloth_filename": cloth_filename
    }


@app.post("/tryon")
def run_tryon(
    person_image: UploadFile = File(...),
    cloth_image: UploadFile | None = File(None),
    cloth_id: str | None = Form(None),
):
    person_filename = make_filename("person", person_image.filename)
    person_path = PERSON_DIR / person_filename

    with person_path.open("wb") as buffer:
        shutil.copyfileobj(person_image.file, buffer)

    if cloth_image is not None:
        cloth_filename = make_filename("cloth", cloth_image.filename)
        cloth_path = CLOTH_DIR / cloth_filename

        with cloth_path.open("wb") as buffer:
            shutil.copyfileobj(cloth_image.file, buffer)

    elif cloth_id:
        cloth_source_path = CLOTHING_STATIC_DIR / cloth_id

        if not cloth_source_path.exists() or not cloth_source_path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"선택한 옷 파일을 찾을 수 없습니다: {cloth_id}"
            )

        cloth_filename = make_filename("cloth", cloth_source_path.name)
        cloth_path = CLOTH_DIR / cloth_filename
        shutil.copy2(cloth_source_path, cloth_path)

    else:
        raise HTTPException(
            status_code=400,
            detail="cloth_image 또는 cloth_id 중 하나는 반드시 필요합니다."
        )

    if not PIPELINE_SCRIPT.exists():
        raise HTTPException(
            status_code=500,
            detail=f"main_pipeline.py 파일을 찾을 수 없습니다: {PIPELINE_SCRIPT}"
        )

    pipeline_python_path = Path(PIPELINE_PYTHON)
    if not pipeline_python_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"파이프라인 Python 실행 파일을 찾을 수 없습니다: {PIPELINE_PYTHON}"
        )

    copy_to_pipeline_input(person_path, cloth_path)

    cmd = [
        PIPELINE_PYTHON,
        str(PIPELINE_SCRIPT),
    ]

    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    print("\n" + "=" * 80, flush=True)
    print("[/tryon 요청 시작]", flush=True)
    print("=" * 80, flush=True)
    print("person_path :", person_path, flush=True)
    print("cloth_path  :", cloth_path, flush=True)
    print("pipeline person dir :", PIPELINE_INPUT_PERSON_DIR, flush=True)
    print("pipeline cloth dir  :", PIPELINE_INPUT_CLOTH_DIR, flush=True)
    print("cmd         :", cmd, flush=True)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(PIPELINE_SCRIPT.parent),
        )

        print("\n[PIPELINE SUCCESS]", flush=True)
        print("returncode:", result.returncode, flush=True)
        print("STDOUT:\n", result.stdout, flush=True)
        print("STDERR:\n", result.stderr, flush=True)

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 80, flush=True)
        print("[PIPELINE FAILED - CalledProcessError]", flush=True)
        print("=" * 80, flush=True)
        print("returncode:", e.returncode, flush=True)
        print("cmd       :", e.cmd, flush=True)
        print("STDOUT:\n", e.stdout, flush=True)
        print("STDERR:\n", e.stderr, flush=True)

        raise HTTPException(
            status_code=500,
            detail={
                "message": "pipeline execution failed",
                "returncode": e.returncode,
                "cmd": e.cmd,
                "stdout": e.stdout,
                "stderr": e.stderr
            }
        )

    except Exception as e:
        print("\n" + "=" * 80, flush=True)
        print("[PIPELINE FAILED - Unexpected Exception]", flush=True)
        print("=" * 80, flush=True)
        print("cmd   :", cmd, flush=True)
        print("error :", str(e), flush=True)
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail={
                "message": "unexpected server error",
                "cmd": cmd,
                "error": str(e)
            }
        )

    latest_job_dir = get_latest_job_dir(RUNS_DIR)
    result_image_path = None
    result_image_url = None

    if latest_job_dir is not None:
        result_image_path, result_image_url = find_result_image_in_job(latest_job_dir)

    return {
        "message": "tryon pipeline executed successfully",
        "person_image": str(person_path),
        "cloth_image": str(cloth_path),
        "job_dir": str(latest_job_dir) if latest_job_dir else None,
        "result_image_path": result_image_path,
        "result_image_url": result_image_url
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)