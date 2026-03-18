import os
from pathlib import Path
from PIL import Image

# 원본 폴더
src_dir = Path(r"C:\Users\asd\Desktop\custom_dataset")

# 출력 폴더
cloth_dir = src_dir / "cloth"
image_dir = src_dir / "image"

cloth_dir.mkdir(exist_ok=True)
image_dir.mkdir(exist_ok=True)

# 허용 확장자
valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# 최종 크기 (가로, 세로)
target_size = (768, 1024)


def convert_to_white_bg_and_resize(src_path: Path, dst_path: Path):
    img = Image.open(src_path).convert("RGBA")

    # 흰 배경 합성
    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    merged = Image.alpha_composite(white_bg, img).convert("RGB")

    # 리사이즈
    merged = merged.resize(target_size, Image.LANCZOS)

    # JPG 저장
    merged.save(dst_path, "JPEG", quality=95)


for file_path in src_dir.iterdir():
    if not file_path.is_file():
        continue

    if file_path.suffix.lower() not in valid_exts:
        continue

    stem = file_path.stem  # 예: 1016713_1
    parts = stem.rsplit("_", 1)

    if len(parts) != 2:
        print(f"[SKIP] 이름 형식 불일치: {file_path.name}")
        continue

    base_name, suffix_num = parts

    if suffix_num == "1":
        dst_folder = cloth_dir
    elif suffix_num == "2":
        dst_folder = image_dir
    else:
        print(f"[SKIP] _1 또는 _2 아님: {file_path.name}")
        continue

    dst_path = dst_folder / f"{base_name}.jpg"

    try:
        convert_to_white_bg_and_resize(file_path, dst_path)
        print(f"[OK] {file_path.name} -> {dst_path}")
    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")

print("완료")