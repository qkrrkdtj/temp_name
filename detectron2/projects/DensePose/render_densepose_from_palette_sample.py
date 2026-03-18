import os
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, "/media/kccistc/1024AC1A24AC0536/Users/asd/Desktop/project/detectron2")
sys.path.insert(0, "/media/kccistc/1024AC1A24AC0536/Users/asd/Desktop/project/detectron2/projects/DensePose")

import torch
import numpy as np
from PIL import Image
from tqdm import tqdm


def load_labels_from_dump(dump_path):
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

    for lbl_str, rgb in palette.items():
        lbl = int(lbl_str)
        patch[labels_r == lbl] = np.array(rgb, dtype=np.uint8)

    canvas[y1:y2, x1:x2] = patch
    return canvas


def render_sample(dump_dir, ref_image_dir, palette_json, out_dir, max_images=20):
    os.makedirs(out_dir, exist_ok=True)

    with open(palette_json, "r", encoding="utf-8") as f:
        raw_palette = json.load(f)

    palette = {k: v["rgb"] if isinstance(v, dict) else v for k, v in raw_palette.items()}

    dump_paths = sorted(glob.glob(os.path.join(dump_dir, "*_densepose_dump.pkl")))

    ok = 0
    fail = 0

    for dump_path in tqdm(dump_paths[:max_images], desc="rendering sample"):
        base = Path(dump_path).stem.replace("_densepose_dump", "")

        ref_img_path = os.path.join(ref_image_dir, f"{base}.jpg")
        if not os.path.exists(ref_img_path):
            ref_img_path = os.path.join(ref_image_dir, f"{base}.png")

        if not os.path.exists(ref_img_path):
            print(f"[WARN] missing ref image: {base}")
            fail += 1
            continue

        try:
            ref_img = Image.open(ref_img_path).convert("RGB")
            w, h = ref_img.size

            labels, box = load_labels_from_dump(dump_path)
            if labels is None:
                out = np.zeros((h, w, 3), dtype=np.uint8)
            else:
                out = render_label_map_to_image(labels, box, h, w, palette)

            out_path = os.path.join(out_dir, f"{base}.jpg")
            Image.fromarray(out).save(out_path)
            ok += 1

        except Exception as e:
            print(f"[WARN] failed {dump_path}: {e}")
            fail += 1

    print(f"\nDone. ok={ok}, fail={fail}")
    print(f"out_dir: {out_dir}")


if __name__ == "__main__":
    dump_dir = "/media/kccistc/1024AC1A24AC0536/Users/asd/Desktop/custom_dataset/densepose_dumps"
    ref_image_dir = "/media/kccistc/1024AC1A24AC0536/Users/asd/Desktop/custom_dataset/image"
    palette_json = "/media/kccistc/1024AC1A24AC0536/Users/asd/Desktop/project/HR-VITON/label_palette.json"
    out_dir = "/media/kccistc/1024AC1A24AC0536/Users/asd/Desktop/custom_dataset/image-densepose"

    render_sample(
        dump_dir=dump_dir,
        ref_image_dir=ref_image_dir,
        palette_json=palette_json,
        out_dir=out_dir,
        max_images=500
    )
