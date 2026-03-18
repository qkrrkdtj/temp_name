from pathlib import Path

dataset_root = Path(r"C:\Users\asd\Desktop\custom_dataset")
cloth_dir = dataset_root / "cloth"
image_dir = dataset_root / "image"

valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def get_stem_map(folder: Path):
    result = {}
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in valid_exts:
            result[p.stem] = p
    return result

cloth_map = get_stem_map(cloth_dir)
image_map = get_stem_map(image_dir)

cloth_names = set(cloth_map.keys())
image_names = set(image_map.keys())

only_in_cloth = cloth_names - image_names
only_in_image = image_names - cloth_names

for name in sorted(only_in_cloth):
    path = cloth_map[name]
    path.unlink()
    print(f"[DELETE cloth only] {path}")

for name in sorted(only_in_image):
    path = image_map[name]
    path.unlink()
    print(f"[DELETE image only] {path}")

print("=" * 60)
print(f"cloth만 있던 파일 삭제: {len(only_in_cloth)}개")
print(f"image만 있던 파일 삭제: {len(only_in_image)}개")
print("완료")