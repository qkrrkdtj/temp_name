import shutil
from pathlib import Path
import sys


REQUIRED_DIRS = [
    "image",
    "cloth",
    "cloth-mask",
    "agnostic-v3.2",
    "agnostic-mask",
    "image-densepose",
]


def ensure_dirs(root: Path):
    for name in REQUIRED_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)


def copy_one(src: Path, dst: Path):
    if not src.exists():
        raise FileNotFoundError(f"필수 파일이 없습니다: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_dataset(job_dir: Path):
    dataset_root = job_dir / "stableviton_dataset"
    test_root = dataset_root / "test"
    ensure_dirs(test_root)

    person_name = "person.jpg"
    cloth_name = "cloth.jpg"
    densepose_name = "person.jpg"
    agnostic_name = "person.jpg"
    agnostic_mask_name = "person_mask.png"
    cloth_mask_name = "cloth.png"   # dataset.py가 cloth 파일명 그대로 찾음

    copy_one(job_dir / "input" / "image" / person_name,
             test_root / "image" / person_name)

    copy_one(job_dir / "input" / "cloth" / cloth_name,
             test_root / "cloth" / cloth_name)

    # cloth-mask는 dataset.py가 cloth.jpg 이름으로 찾으므로 jpg 이름 유지
    copy_one(job_dir / "preprocess" / "cloth-mask" / "cloth.png",
             test_root / "cloth-mask" / cloth_mask_name)

    copy_one(job_dir / "preprocess" / "agnostic-v3.2" / agnostic_name,
             test_root / "agnostic-v3.2" / agnostic_name)

    copy_one(job_dir / "preprocess" / "agnostic-mask" / agnostic_mask_name,
             test_root / "agnostic-mask" / agnostic_mask_name)

    copy_one(job_dir / "preprocess" / "image-densepose" / densepose_name,
             test_root / "image-densepose" / densepose_name)

    pair_file = dataset_root / "test_pairs.txt"
    pair_file.write_text(f"{person_name} {cloth_name}\n", encoding="utf-8")

    print("[DONE] StableVITON test dataset 정리 완료")
    print(" - dataset root:", dataset_root)
    print(" - pair file   :", pair_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("사용법: python build_stableviton_dataset.py <job_dir>")
    job_dir = Path(sys.argv[1])
    build_dataset(job_dir)