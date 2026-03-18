import subprocess
import sys
from pathlib import Path


def run_make_agnostic_mask(job_dir: Path):
    script_path = Path(__file__).resolve().parent / "make_agnostic_mask.py"
    dataset_root = job_dir / "preprocess"

    cmd = [
        sys.executable,
        str(script_path),
        "--data_root", str(dataset_root),
        "--image_dir", "image",
        # "--parse_dir", "image-parse-v3/cihp_parsing_maps",
        "--parse_dir", "image-parse-v3",
        "--pose_dir", "openpose_json",
        "--agnostic_dir", "agnostic-v3.2",
        "--mask_dir", "agnostic-mask",
        "--ext", ".jpg",
    ]


    print("[INFO] make_agnostic_mask command:", " ".join(cmd))
    result = subprocess.run(cmd, text=True)

    if result.returncode != 0:
        raise RuntimeError("make_agnostic_mask.py 실행 실패")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_make_agnostic_mask.py <job_dir>")
    job_dir = Path(sys.argv[1])

    # preprocess/image 폴더가 필요하므로 person.jpg를 복사
    src = job_dir / "input" / "image" / "person.jpg"
    dst_dir = job_dir / "preprocess" / "image"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "person.jpg"

    if not dst.exists():
        import shutil
        shutil.copy2(src, dst)

    run_make_agnostic_mask(job_dir)