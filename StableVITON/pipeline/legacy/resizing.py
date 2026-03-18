import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image

# 원본 폴더
dataset_root = Path(r"C:\Users\asd\Desktop\custom_dataset")

cloth_dir = dataset_root / "cloth"
image_dir = dataset_root / "image"

# 임시 폴더
temp_root = dataset_root / "_white_bg_temp"
rgba_root = dataset_root / "_white_bg_rgba"

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


def run_carvekit(input_dir: Path, output_dir: Path, python_exe=None, device="gpu"):
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


def composite_white_bg(rgba_path: Path, out_path: Path, size=TARGET_SIZE):
    rgba = Image.open(rgba_path).convert("RGBA").resize(size, Image.LANCZOS)
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white, rgba).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comp.save(out_path, "JPEG", quality=95)


def process_folder(folder: Path, folder_name: str, python_exe=None, device="gpu"):
    files = collect_images(folder)
    if not files:
        print(f"[SKIP] 이미지 없음: {folder}")
        return

    print(f"\n{'=' * 70}")
    print(f"[START] {folder_name} 처리 시작")
    print(f"{'=' * 70}")

    temp_input_dir = temp_root / folder_name
    rgba_output_dir = rgba_root / folder_name

    clean_dir(temp_input_dir)
    clean_dir(rgba_output_dir)

    # 1) 원본들 임시 입력 폴더에 768x1024 jpg로 통일 저장
    for src in files:
        dst = temp_input_dir / f"{src.stem}.jpg"
        resize_to_target(src, dst)
        print(f"[RESIZE] {src.name} -> {dst.name}")

    # 2) carvekit으로 배경 제거
    run_carvekit(temp_input_dir, rgba_output_dir, python_exe=python_exe, device=device)

    # 3) 흰 배경 합성 후 원래 폴더에 다시 저장
    for src in files:
        rgba_jpg = rgba_output_dir / f"{src.stem}.jpg"
        rgba_png = rgba_output_dir / f"{src.stem}.png"

        rgba_path = rgba_jpg if rgba_jpg.exists() else rgba_png

        if not rgba_path.exists():
            print(f"[SKIP] carvekit 결과 없음: {src.name}")
            continue

        out_path = folder / f"{src.stem}.jpg"
        composite_white_bg(rgba_path, out_path)
        print(f"[DONE] {src.name} -> {out_path.name}")

        # 원본이 jpg가 아니면 남겨둘지 삭제할지 선택
        if src.suffix.lower() != ".jpg" or src.name != out_path.name:
            try:
                src.unlink()
                print(f"[DELETE] 원본 삭제: {src.name}")
            except Exception as e:
                print(f"[WARN] 원본 삭제 실패: {src.name} / {e}")

    print(f"{'=' * 70}")
    print(f"[END] {folder_name} 처리 완료")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    # carvekit이 설치된 파이썬 실행파일 경로
    # 같은 가상환경에서 실행하면 None으로 둬도 됨
    python_exe = sys.executable

    # cpu 또는 cuda
    device = "cuda"

    process_folder(cloth_dir, "cloth", python_exe=python_exe, device=device)
    process_folder(image_dir, "image", python_exe=python_exe, device=device)

    print("\n전체 완료")