import subprocess
import sys
from pathlib import Path
from datetime import datetime
import shutil

from config import RUNS_ROOT, STABLEVITON_ROOT

SCRIPTS = [
    "run_prepare_inputs.py",
    "run_openpose.py",
    "run_schp.py",
    "run_densepose.py",
    "run_cloth_mask.py",
    "run_make_agnostic_mask.py",
    "build_stableviton_dataset.py",
]


def create_job_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    job_dir = RUNS_ROOT / f"job_{timestamp}"

    (job_dir / "input" / "image").mkdir(parents=True, exist_ok=True)
    (job_dir / "input" / "cloth").mkdir(parents=True, exist_ok=True)
    (job_dir / "temp").mkdir(parents=True, exist_ok=True)

    (job_dir / "preprocess" / "openpose_json").mkdir(parents=True, exist_ok=True)
    (job_dir / "preprocess" / "openpose_img").mkdir(parents=True, exist_ok=True)
    (job_dir / "preprocess" / "image-parse-v3").mkdir(parents=True, exist_ok=True)
    (job_dir / "preprocess" / "image-densepose").mkdir(parents=True, exist_ok=True)
    (job_dir / "preprocess" / "cloth-mask").mkdir(parents=True, exist_ok=True)
    (job_dir / "preprocess" / "person-rgba").mkdir(parents=True, exist_ok=True)
    (job_dir / "preprocess" / "cloth-rgba").mkdir(parents=True, exist_ok=True)

    return job_dir


def safe_remove(path: Path):
    if not path.exists():
        print(f"[SKIP] 없음: {path}")
        return

    if path.is_file():
        path.unlink()
        print(f"[DEL FILE] {path}")
    elif path.is_dir():
        shutil.rmtree(path)
        print(f"[DEL DIR]  {path}")


def clear_folder_contents(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)

    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
            print(f"[DEL FILE] {item}")
        elif item.is_dir():
            shutil.rmtree(item)
            print(f"[DEL DIR]  {item}")


def cleanup_after_inference(job_dir: Path):
    print("\n" + "=" * 70)
    print("[자동 정리 시작]")
    print("=" * 70)

    targets = [
        job_dir / "stableviton_dataset",
        job_dir / "input",
        job_dir / "preprocess",
        job_dir / "temp",
    ]

    for target in targets:
        safe_remove(target)

    input_drop_cloth = Path(__file__).resolve().parent / "input_drop" / "cloth"
    input_drop_person = Path(__file__).resolve().parent / "input_drop" / "person"

    clear_folder_contents(input_drop_cloth)
    clear_folder_contents(input_drop_person)

    print("\n[자동 정리 완료]")
    print(f"남겨진 결과 폴더: {job_dir / 'results'}")


def run_script(script_name: str, job_dir: Path):
    script_path = Path(__file__).resolve().parent / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"스크립트가 없습니다: {script_path}")

    print("=" * 70)
    print(f"[실행 시작] {script_name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, str(script_path), str(job_dir)],
        text=True,
        cwd=str(script_path.parent),
    )

    print(f"[INFO] {script_name} returncode = {result.returncode}")
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} 실행 실패")


def run_stableviton_inference(job_dir: Path):
    dataset_root = job_dir / "stableviton_dataset"
    output_dir = job_dir / "results"

    inference_script = STABLEVITON_ROOT / "inference.py"
    config_path = STABLEVITON_ROOT / "configs" / "VITONHD.yaml"
    model_path = STABLEVITON_ROOT / "ckpts" / "VITONHD.ckpt"

    if not inference_script.exists():
        raise FileNotFoundError(f"inference.py가 없습니다: {inference_script}")
    if not config_path.exists():
        raise FileNotFoundError(f"config가 없습니다: {config_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"가중치가 없습니다: {model_path}")

    cmd = [
        sys.executable,
        str(inference_script),
        "--config_path", str(config_path),
        "--model_load_path", str(model_path),
        "--data_root_dir", str(dataset_root),
        "--save_dir", str(output_dir),
        "--batch_size", "1",
        "--unpair",
    ]

    print("\n" + "=" * 70)
    print("[StableVITON 추론 시작]")
    print("=" * 70)
    print(" ".join(cmd))

    result = subprocess.run(
        cmd,
        text=True,
        cwd=str(STABLEVITON_ROOT),
    )

    print(f"[INFO] inference.py returncode = {result.returncode}")
    if result.returncode != 0:
        raise RuntimeError("inference.py 실행 실패")

    print("[추론 완료]")
    print(f"결과 폴더: {output_dir}")


def main():
    job_dir = create_job_dir()

    print("=" * 70)
    print("[JOB 생성 완료]")
    print(job_dir)
    print("=" * 70)
    print("[파이프라인 흐름]")
    print("사람/의상 입력 -> 768x1024 리사이즈 -> 흰 배경 합성 -> OpenPose / SCHP / DensePose / Cloth Mask / Parse Agnostic -> dataset 정리 -> 추론")

    try:
        for script in SCRIPTS:
            run_script(script, job_dir)

        run_stableviton_inference(job_dir)
        cleanup_after_inference(job_dir)
    except Exception as e:
        print(f"[ERROR] 파이프라인 중단: {e}")
        print(f"[INFO] 디버깅을 위해 중간 결과를 보존합니다: {job_dir}")
        raise

    print("\n" + "=" * 70)
    print("[전체 파이프라인 완료]")
    print("=" * 70)
    print(f"JOB 폴더                : {job_dir}")
    print(f"최종 결과 폴더           : {job_dir / 'results'}")
    print(f"그리드 결과 폴더         : {job_dir / 'results' / 'grid'}")


if __name__ == "__main__":
    main()
