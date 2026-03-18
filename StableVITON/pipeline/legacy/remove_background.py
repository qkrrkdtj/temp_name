import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image

# 원본 폴더
dataset_root = Path(r"C:\Users\asd\Desktop\custom_dataset\train")

cloth_dir = dataset_root / "cloth"
image_dir = dataset_root / "image"

# 임시 폴더
temp_root = dataset_root / "_rgba_temp"
carvekit_root = dataset_root / "_rgba_carvekit"

# 최종 출력 폴더
cloth_rgba_dir = dataset_root / "cloth-rgba"

TARGET_SIZE = (768, 1024)
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def clean_dir(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def collect_images(folder: Path):
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTS])


def resize_to_target(src: Path, dst: Path, size=TARGET_SIZE):
    dst.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img = img.resize(size, Image.LANCZOS)
    img.save(dst, "JPEG", quality=95)


def run_carvekit(input_dir: Path, output_dir: Path, python_exe=None, device="cuda"):
    clean_dir(output_dir)

    python_cmd = python_exe if python_exe else sys.executable

    cmd = [
        python_cmd,
        "-m",
        "carvekit",
        "-i",
        str(input_dir),
        "-o",
        str(output_dir),
        "--device",
        device,
    ]

    print("[INFO] carvekit command:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")

    if result.stdout:
        print("[carvekit stdout]")
        print(result.stdout)

    if result.returncode != 0:
        if result.stderr:
            print("[carvekit stderr]")
            print(result.stderr)
        raise RuntimeError("carvekit 실행 실패")


def save_as_rgba_png(src_path: Path, dst_path: Path, size=TARGET_SIZE):
    img = Image.open(src_path).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst_path, "PNG")


def process_folder(input_folder: Path, folder_name: str, final_output_dir: Path, python_exe=None, device="cuda"):
    files = collect_images(input_folder)
    if not files:
        print(f"[SKIP] 이미지 없음: {input_folder}")
        return

    print(f"\n{'=' * 70}")
    print(f"[START] {folder_name} RGBA 생성 시작")
    print(f"{'=' * 70}")

    temp_input_dir = temp_root / folder_name
    carvekit_output_dir = carvekit_root / folder_name

    clean_dir(temp_input_dir)
    clean_dir(carvekit_output_dir)
    clean_dir(final_output_dir)

    # 1) carvekit 입력용으로 768x1024 jpg 통일
    for src in files:
        dst = temp_input_dir / f"{src.stem}.jpg"
        resize_to_target(src, dst)
        print(f"[RESIZE] {src.name} -> {dst.name}")

    # 2) carvekit 실행
    run_carvekit(temp_input_dir, carvekit_output_dir, python_exe=python_exe, device=device)

    # 3) carvekit 결과를 RGBA PNG로 최종 저장
    for src in files:
        candidate_png = carvekit_output_dir / f"{src.stem}.png"
        candidate_jpg = carvekit_output_dir / f"{src.stem}.jpg"
        candidate_webp = carvekit_output_dir / f"{src.stem}.webp"

        if candidate_png.exists():
            carved_path = candidate_png
        elif candidate_jpg.exists():
            carved_path = candidate_jpg
        elif candidate_webp.exists():
            carved_path = candidate_webp
        else:
            print(f"[SKIP] carvekit 결과 없음: {src.name}")
            continue

        out_path = final_output_dir / f"{src.stem}.png"
        save_as_rgba_png(carved_path, out_path)
        print(f"[DONE] {src.name} -> {out_path}")

    print(f"{'=' * 70}")
    print(f"[END] {folder_name} RGBA 생성 완료")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    # carvekit 설치된 환경의 python
    python_exe = sys.executable

    # "cuda" 또는 "cpu"
    device = "cuda"

    process_folder(cloth_dir, "cloth", cloth_rgba_dir, python_exe=python_exe, device=device)

    print("\n전체 완료")