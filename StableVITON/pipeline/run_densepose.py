import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

import torch
import numpy as np
from PIL import Image

from config import (
    DENSEPOSE_ROOT,
    DENSEPOSE_MODEL,
    DENSEPOSE_PALETTE_JSON,
    CONDA_ENV,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def clean_dir(dir_path: Path):
    dir_path.mkdir(parents=True, exist_ok=True)
    for item in dir_path.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def pick_first_image(folder: Path) -> Path:
    files = sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    )
    if not files:
        raise FileNotFoundError(f"이미지가 없습니다: {folder}")
    return files[0]


def to_wsl_path(win_path: Path) -> str:
    s = str(win_path).replace("\\", "/")
    drive = s[0].lower()
    rest = s[2:]
    return f"/mnt/{drive}{rest}"


def load_palette(json_path: Path):
    if not json_path.exists():
        raise FileNotFoundError(f"palette json 파일이 없습니다: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        raw_palette = json.load(f)

    # label_palette.json 구조:
    # {
    #   "1": {"rgb": [37,60,162], "count": 39972},
    #   ...
    # }
    palette = {}
    for k, v in raw_palette.items():
        if isinstance(v, dict) and "rgb" in v:
            palette[int(k)] = np.array(v["rgb"], dtype=np.uint8)
        else:
            palette[int(k)] = np.array(v, dtype=np.uint8)

    return palette


def run_densepose_dump(image_path: Path, dump_path: Path):
    dump_path.parent.mkdir(parents=True, exist_ok=True)

    apply_net_path = DENSEPOSE_ROOT / "apply_net.py"
    if not apply_net_path.exists():
        raise FileNotFoundError(f"apply_net.py 없음: {apply_net_path}")

    model_arg = str(DENSEPOSE_MODEL)

    if model_arg.startswith("http://") or model_arg.startswith("https://"):
        model_wsl = model_arg
    else:
        model_path = Path(model_arg)
        if not model_path.exists():
            raise FileNotFoundError(f"DensePose 모델 파일 없음: {model_path}")
        model_wsl = to_wsl_path(model_path)

    image_path_wsl = to_wsl_path(image_path)
    dump_path_wsl = to_wsl_path(dump_path)
    apply_net_wsl = to_wsl_path(apply_net_path)
    densepose_root_wsl = to_wsl_path(DENSEPOSE_ROOT)

    cmd = [
        "wsl",
        "bash",
        "-lc",
        (
            "source ~/miniconda3/etc/profile.d/conda.sh && "
            f"conda activate {CONDA_ENV} && "
            f"cd {densepose_root_wsl} && "
            f"python {apply_net_wsl} dump "
            f"configs/densepose_rcnn_R_50_FPN_s1x.yaml "
            f"{model_wsl} "
            f"{image_path_wsl} "
            f"--output {dump_path_wsl}"
        )
    ]

    print("[INFO] DensePose dump command:")
    print(" ".join(cmd))

    result = subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True
    )

    print("\n[DensePose STDOUT]")
    print(result.stdout)
    print("\n[DensePose STDERR]")
    print(result.stderr)
    print(f"[INFO] DensePose returncode = {result.returncode}")

    if result.returncode != 0:
        raise RuntimeError("DensePose dump 생성 실패")


def load_labels_and_box_from_dump(dump_path: Path):
    data = torch.load(dump_path, map_location="cpu", weights_only=False)

    if not isinstance(data, list) or len(data) == 0:
        return None, None

    item = data[0]
    scores = item.get("scores", None)
    pred_boxes = item.get("pred_boxes_XYXY", None)
    pred_densepose = item.get("pred_densepose", None)

    if pred_densepose is None or len(pred_densepose) == 0:
        return None, None

    if scores is None or len(scores) == 0:
        best_idx = 0
    else:
        best_idx = int(torch.argmax(scores).item())

    box = pred_boxes[best_idx].cpu().numpy()
    dp = pred_densepose[best_idx]
    labels = dp.labels.cpu().numpy().astype(np.uint8)

    return labels, box


def render_label_map_to_image(labels, box, out_h, out_w, palette):
    canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    x1, y1, x2, y2 = box
    x1, y1, x2, y2 = map(int, [round(x1), round(y1), round(x2), round(y2)])

    x1 = max(0, min(x1, out_w - 1))
    x2 = max(0, min(x2, out_w))
    y1 = max(0, min(y1, out_h - 1))
    y2 = max(0, min(y2, out_h))

    bw = x2 - x1
    bh = y2 - y1

    if bw <= 0 or bh <= 0:
        return canvas

    labels_img = Image.fromarray(labels, mode="L").resize((bw, bh), Image.NEAREST)
    labels_r = np.array(labels_img, dtype=np.uint8)

    patch = np.zeros((bh, bw, 3), dtype=np.uint8)

    for lbl, rgb in palette.items():
        patch[labels_r == lbl] = rgb

    canvas[y1:y2, x1:x2] = patch
    return canvas

def render_densepose_in_wsl(image_path: Path, dump_path: Path, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    image_path_wsl = to_wsl_path(image_path)
    dump_path_wsl = to_wsl_path(dump_path)
    out_path_wsl = to_wsl_path(out_path)
    palette_wsl = to_wsl_path(DENSEPOSE_PALETTE_JSON)
    densepose_root_wsl = to_wsl_path(DENSEPOSE_ROOT)

    render_code = rf"""
import json
import torch
import numpy as np
from PIL import Image

def load_palette(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        raw_palette = json.load(f)
    palette = {{}}
    for k, v in raw_palette.items():
        if isinstance(v, dict) and "rgb" in v:
            palette[int(k)] = np.array(v["rgb"], dtype=np.uint8)
        else:
            palette[int(k)] = np.array(v, dtype=np.uint8)
    return palette

def load_labels_and_box_from_dump(dump_path):
    data = torch.load(dump_path, map_location="cpu", weights_only=False)
    if not isinstance(data, list) or len(data) == 0:
        return None, None

    item = data[0]
    scores = item.get("scores", None)
    pred_boxes = item.get("pred_boxes_XYXY", None)
    pred_densepose = item.get("pred_densepose", None)

    if pred_densepose is None or len(pred_densepose) == 0:
        return None, None

    if scores is None or len(scores) == 0:
        best_idx = 0
    else:
        best_idx = int(torch.argmax(scores).item())

    box = pred_boxes[best_idx].cpu().numpy()
    dp = pred_densepose[best_idx]
    labels = dp.labels.cpu().numpy().astype(np.uint8)
    return labels, box

def render_label_map_to_image(labels, box, out_h, out_w, palette):
    canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    x1, y1, x2, y2 = box
    x1, y1, x2, y2 = map(int, [round(x1), round(y1), round(x2), round(y2)])

    x1 = max(0, min(x1, out_w - 1))
    x2 = max(0, min(x2, out_w))
    y1 = max(0, min(y1, out_h - 1))
    y2 = max(0, min(y2, out_h))

    bw = x2 - x1
    bh = y2 - y1
    if bw <= 0 or bh <= 0:
        return canvas

    labels_img = Image.fromarray(labels, mode="L").resize((bw, bh), Image.NEAREST)
    labels_r = np.array(labels_img, dtype=np.uint8)

    patch = np.zeros((bh, bw, 3), dtype=np.uint8)
    for lbl, rgb in palette.items():
        patch[labels_r == lbl] = rgb

    canvas[y1:y2, x1:x2] = patch
    return canvas

ref_img = Image.open(r"{image_path_wsl}").convert("RGB")
out_w, out_h = ref_img.size
labels, box = load_labels_and_box_from_dump(r"{dump_path_wsl}")

if labels is None or box is None:
    out = np.zeros((out_h, out_w, 3), dtype=np.uint8)
else:
    palette = load_palette(r"{palette_wsl}")
    out = render_label_map_to_image(labels, box, out_h, out_w, palette)

Image.fromarray(out).save(r"{out_path_wsl}", "JPEG", quality=95)
print("saved:", r"{out_path_wsl}")
"""

    cmd = [
        "wsl",
        "bash",
        "-lc",
        (
            "source ~/miniconda3/etc/profile.d/conda.sh && "
            f"conda activate {CONDA_ENV} && "
            f"cd {densepose_root_wsl} && "
            f"python -c '{render_code}'"
        )
    ]

    result = subprocess.run(cmd, text=True, encoding="utf-8", errors="ignore")
    print(f"[INFO] DensePose render returncode = {result.returncode}")
    if result.returncode != 0:
        raise RuntimeError("DensePose render 생성 실패")


def run_densepose(paths: dict):
    image_dir = paths["image_dir"]
    dump_dir = paths["dump_dir"]
    out_dir = paths["out_dir"]

    clean_dir(dump_dir)
    clean_dir(out_dir)

    image_path = pick_first_image(image_dir)
    base_stem = image_path.stem

    dump_path = dump_dir / f"{base_stem}_densepose_dump.pkl"
    out_path = out_dir / f"{base_stem}.jpg"

    print(f"[INFO] input image       : {image_path}")
    print(f"[INFO] densepose dump   : {dump_path}")
    print(f"[INFO] densepose output : {out_path}")
    print(f"[INFO] palette json     : {DENSEPOSE_PALETTE_JSON}")

    run_densepose_dump(image_path, dump_path)

    if not dump_path.exists():
        raise FileNotFoundError(f"dump 결과 파일이 없습니다: {dump_path}")

    render_densepose_in_wsl(image_path, dump_path, out_path)

    if not out_path.exists():
        raise FileNotFoundError(f"densepose 이미지 결과가 없습니다: {out_path}")

    print("[DONE] DensePose 완료")
    print(f" - dump : {dump_path}")
    print(f" - image: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_densepose.py <job_dir>")
    job_dir = Path(sys.argv[1])

    paths = {
        "image_dir": job_dir / "input" / "image",
        "dump_dir": job_dir / "preprocess" / "densepose_dumps",
        "out_dir": job_dir / "preprocess" / "image-densepose",
    }

    run_densepose(paths)