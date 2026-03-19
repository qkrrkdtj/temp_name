import os
import sys
import glob
import subprocess
from pathlib import Path
from tqdm import tqdm

# 프로젝트 경로
DETECTRON2_PATH = "/path/detectron2"
DENSEPOSE_PATH = "/path/detectron2/projects/DensePose"

CONFIG_PATH = "/path/densepose_rcnn_R_50_FPN_s1x.yaml"
MODEL_PATH = "https://dl.fbaipublicfiles.com/densepose/densepose_rcnn_R_50_FPN_s1x/165712039/model_final_162be9.pkl"
APPLY_NET_PATH = "/path/detectron2/projects/DensePose/apply_net.py"

PYTHONPATH_VALUE = f"{DETECTRON2_PATH}:{DENSEPOSE_PATH}:" + os.environ.get("PYTHONPATH", "")


def collect_images(image_dir):
    exts = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(image_dir, ext)))
    return sorted(files)


def run_dump(img_path, dump_path):
    cmd = [
        "python",
        APPLY_NET_PATH,
        "dump",
        CONFIG_PATH,
        MODEL_PATH,
        img_path,
        "--output",
        dump_path,
    ]

    result = subprocess.run(
        cmd,
        env={**os.environ, "PYTHONPATH": PYTHONPATH_VALUE},
        text=True,
    )
    return result


def main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("python batch_densepose_dump.py <image_dir> <dump_dir>")
        sys.exit(1)

    image_dir = sys.argv[1]
    dump_dir = sys.argv[2]

    os.makedirs(dump_dir, exist_ok=True)

    image_paths = collect_images(image_dir)
    print(f"found {len(image_paths)} images")

    ok_count = 0
    fail_count = 0

    for img_path in tqdm(image_paths, desc="dumping"):
        base = Path(img_path).stem
        dump_path = os.path.join(dump_dir, f"{base}_densepose_dump.pkl")

        result = run_dump(img_path, dump_path)
        if result.returncode != 0:
            fail_count += 1
            print(f"\n[ERROR] dump failed: {img_path}")
            continue

        ok_count += 1

    print(f"\nDone. ok={ok_count}, fail={fail_count}")
    print("dump_dir:", dump_dir)


if __name__ == "__main__":
    main()
