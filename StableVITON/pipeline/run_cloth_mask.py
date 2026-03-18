from pathlib import Path
from PIL import Image
import shutil
import sys
from postprocess_cloth_mask import postprocess_cloth_mask


def clean_dir(dir_path: Path):
    dir_path.mkdir(parents=True, exist_ok=True)
    for item in dir_path.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def create_cloth_masks(rgba_dir: Path, mask_dir: Path, size=(768, 1024)):
    clean_dir(mask_dir)
    rgba_files = sorted(list(rgba_dir.glob('*.png')) + list(rgba_dir.glob('*.jpg')))
    if not rgba_files:
        raise FileNotFoundError(f'RGBA 파일이 없습니다: {rgba_dir}')

    success_count = 0
    for input_path in rgba_files:
        output_path = mask_dir / f'{input_path.stem}.png'
        img = Image.open(input_path)

        if 'A' not in img.getbands():
            raise RuntimeError(f'알파 채널이 없습니다: {input_path.name}')

        alpha = img.getchannel('A')
        mask = alpha.point(lambda p: 255 if p >= 128 else 0).convert('L')
        mask = mask.resize(size, Image.NEAREST)
        mask = mask.point(lambda p: 255 if p >= 128 else 0)
        mask.save(output_path, 'PNG')
        print(f'[cloth_mask 완료] {output_path.name} | min/max={mask.getextrema()}')
        postprocess_cloth_mask(output_path)
        success_count += 1

    if success_count == 0:
        raise RuntimeError('cloth_mask가 1개도 생성되지 않았습니다.')
    print(f'[DONE] cloth_mask 생성 완료: {success_count}개')


def run_pipeline(job_dir: Path):
    rgba_dir = job_dir / 'preprocess' / 'cloth-rgba'
    mask_dir = job_dir / 'preprocess' / 'cloth-mask'
    create_cloth_masks(rgba_dir, mask_dir, size=(768, 1024))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_cloth_mask.py <job_dir>")
    job_dir = Path(sys.argv[1])
    run_pipeline(job_dir)
