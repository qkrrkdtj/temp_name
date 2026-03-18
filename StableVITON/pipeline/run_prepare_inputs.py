import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image

from config import PIPELINE_ROOT

ALLOWED_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
TARGET_SIZE = (768, 1024)  # (width, height)

def write_test_pairs(dataset_root: Path):
    dataset_root.mkdir(parents=True, exist_ok=True)
    pairs_path = dataset_root / "test_pairs.txt"
    with open(pairs_path, "w", encoding="utf-8") as f:
        f.write("person.jpg cloth.jpg\n")
    print("생성 완료:", pairs_path)

def collect_images(folder: Path):
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTS])


def pick_first_image(folder: Path) -> Path:
    files = collect_images(folder)
    if not files:
        raise FileNotFoundError(f'이미지가 없습니다: {folder}')
    return files[0]


def clean_dir(dir_path: Path):
    dir_path.mkdir(parents=True, exist_ok=True)
    for item in dir_path.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def resize_to_target(src: Path, dst: Path, size=TARGET_SIZE):
    dst.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    img.save(dst)


def run_carvekit(input_dir: Path, output_dir: Path, device: str = 'cpu'):
    clean_dir(output_dir)
    cmd = [
        sys.executable, '-m', 'carvekit',
        '-i', str(input_dir),
        '-o', str(output_dir),
        '--device', device,
    ]
    print('[INFO] carvekit command:', ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print('[carvekit stdout]')
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print('[carvekit stderr]')
            print(result.stderr)
        raise RuntimeError('carvekit 실행 실패')


def composite_white_bg(rgba_path: Path, out_path: Path, mode: str = 'JPEG', quality: int = 95, size=TARGET_SIZE):
    rgba = Image.open(rgba_path).convert('RGBA').resize(size, Image.LANCZOS)
    white = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white, rgba).convert('RGB')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if mode.upper() == 'JPEG':
        comp.save(out_path, 'JPEG', quality=quality)
    else:
        comp.save(out_path, mode.upper())


def run_prepare_inputs(job_dir: Path, device: str = 'cpu'):
    person_src = pick_first_image(PIPELINE_ROOT / 'input_drop' / 'person')
    cloth_src = pick_first_image(PIPELINE_ROOT / 'input_drop' / 'cloth')

    person_raw_dir = job_dir / 'temp' / 'person_raw'
    cloth_raw_dir = job_dir / 'temp' / 'cloth_raw'
    person_rgba_dir = job_dir / 'preprocess' / 'person-rgba'
    cloth_rgba_dir = job_dir / 'preprocess' / 'cloth-rgba'

    person_raw_dir.mkdir(parents=True, exist_ok=True)
    cloth_raw_dir.mkdir(parents=True, exist_ok=True)

    person_resized = person_raw_dir / 'person.jpg'
    cloth_resized = cloth_raw_dir / 'cloth.jpg'

    # 1) 해상도 통일
    resize_to_target(person_src, person_resized)
    resize_to_target(cloth_src, cloth_resized)

    # 2) 배경 제거 후 흰 배경 합성
    run_carvekit(person_raw_dir, person_rgba_dir, device=device)
    run_carvekit(cloth_raw_dir, cloth_rgba_dir, device=device)

    person_rgba = person_rgba_dir / 'person.jpg'
    cloth_rgba = cloth_rgba_dir / 'cloth.jpg'

    if not person_rgba.exists():
        # carvekit이 png로 저장했을 가능성 대비
        person_rgba = person_rgba_dir / 'person.png'
    if not cloth_rgba.exists():
        # carvekit이 png로 저장했을 가능성 대비
        cloth_rgba = cloth_rgba_dir / 'cloth.png'

    if not person_rgba.exists():
        raise FileNotFoundError(f'사람 RGBA 결과가 없습니다: {person_rgba_dir}')
    if not cloth_rgba.exists():
        raise FileNotFoundError(f'의상 RGBA 결과가 없습니다: {cloth_rgba_dir}')

    # 둘 다 jpg로 저장
    composite_white_bg(person_rgba, job_dir / 'input' / 'image' / 'person.jpg', mode='JPEG')
    composite_white_bg(cloth_rgba, job_dir / 'input' / 'cloth' / 'cloth.jpg', mode='JPEG')

    print('[DONE] 입력 준비 완료')
    print(' - person:', job_dir / 'input' / 'image' / 'person.jpg')
    print(' - cloth :', job_dir / 'input' / 'cloth' / 'cloth.jpg')
    print(' - person rgba:', person_rgba)
    print(' - cloth rgba :', cloth_rgba)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_prepare_inputs.py <job_dir>")
    job_dir = Path(sys.argv[1])
    run_prepare_inputs(job_dir, device='cpu')