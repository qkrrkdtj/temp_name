import subprocess
from pathlib import Path
import sys
from config import OPENPOSE_ROOT


def run_openpose(paths):
    image_dir = paths["image_dir"]
    openpose_json_dir = paths["openpose_json_dir"]
    openpose_img_dir = paths["openpose_img_dir"]

    openpose_json_dir.mkdir(parents=True, exist_ok=True)
    openpose_img_dir.mkdir(parents=True, exist_ok=True)

    exe_file = OPENPOSE_ROOT / "bin" / "OpenPoseDemo.exe"
    if not exe_file.exists():
        raise FileNotFoundError(f"OpenPoseDemo.exe 없음: {exe_file}")

    has_image = False
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        if list(image_dir.glob(ext)):
            has_image = True
            break

    if not has_image:
        raise FileNotFoundError(f"입력 사람 이미지가 없습니다: {image_dir}")

    cmd = [
        str(exe_file),
        "--image_dir", str(image_dir),
        "--disable_blending",
        "--display", "0",
        "--write_json", str(openpose_json_dir),
        "--write_images", str(openpose_img_dir),
    ]

    print("[INFO] OpenPose command:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(OPENPOSE_ROOT),
        encoding="utf-8",
        errors="ignore"
    )

    print("\n[OpenPose STDOUT]\n", result.stdout)
    print("\n[OpenPose STDERR]\n", result.stderr)

    if result.returncode != 0:
        raise RuntimeError("OpenPose 실행 실패")

    print("[DONE] OpenPose 완료")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_openpose.py <job_dir>")
    job_dir = Path(sys.argv[1])

    paths = {
        "job_dir": job_dir,
        "image_dir": job_dir / "input" / "image",
        "openpose_json_dir": job_dir / "preprocess" / "openpose_json",
        "openpose_img_dir": job_dir / "preprocess" / "openpose_img",
    }

    run_openpose(paths)