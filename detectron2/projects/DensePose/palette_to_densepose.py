import os
import glob
import json
from pathlib import Path
from collections import defaultdict, Counter
import sys

sys.path.insert(0, "/path")
sys.path.insert(0, "/path")

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


def make_full_label_map(labels, box, image_w, image_h):
    x1, y1, x2, y2 = box
    x1, y1, x2, y2 = map(int, [round(x1), round(y1), round(x2), round(y2)])

    x1 = max(0, min(x1, image_w - 1))
    x2 = max(0, min(x2, image_w))
    y1 = max(0, min(y1, image_h - 1))
    y2 = max(0, min(y2, image_h))

    bw = x2 - x1
    bh = y2 - y1

    if bw <= 0 or bh <= 0:
	return None

    labels_img = Image.fromarray(labels, mode="L").resize((bw, bh), Image.NEAREST)
    labels_r = np.array(labels_img, dtype=np.uint8)

    full_map = np.zeros((image_h, image_w), dtype=np.uint8)
    full_map[y1:y2, x1:x2] = labels_r
    return full_map


def extract_palette(orig_densepose_dir, dump_dir, output_json, max_images=100):
    orig_paths = sorted(glob.glob(os.path.join(orig_densepose_dir, "*.jpg")))
    color_votes = defaultdict(Counter)

    used = 0
    skipped = 0

    for orig_path in tqdm(orig_paths, desc="extracting palette"):
	base = Path(orig_path).stem
	dump_path = os.path.join(dump_dir, f"{base}_densepose_dump.pkl")

	if not os.path.exists(dump_path):
	    skipped += 1
	    continue

	try:
	    orig_img = Image.open(orig_path).convert("RGB")
	    orig_np = np.array(orig_img, dtype=np.uint8)
	    h, w = orig_np.shape[:2]

	    labels, box = load_labels_from_dump(dump_path)
	    if labels is None:
	        skipped += 1
	        continue

	    label_map = make_full_label_map(labels, box, w, h)
	    if label_map is None:
	        skipped += 1
	        continue

	    ys, xs = np.where(label_map > 0)
	    for y, x in zip(ys, xs):
	        lbl = int(label_map[y, x])
	        rgb = tuple(int(v) for v in orig_np[y, x])
	        color_votes[lbl][rgb] += 1

	    used += 1
	    if used >= max_images:
	        break

	except Exception as e:
	    print(f"[WARN] skipped {orig_path}: {e}")
	    skipped += 1

    palette = {}
    for lbl, counter in sorted(color_votes.items()):
	if len(counter) == 0:
	    continue
	rgb, count = counter.most_common(1)[0]
	palette[lbl] = {
	    "rgb": list(rgb),
	    "count": int(count),
	}

    with open(output_json, "w", encoding="utf-8") as f:
	json.dump(palette, f, indent=2, ensure_ascii=False)

    print(f"\\nSaved palette to: {output_json}")
    print(f"used images   : {used}")
    print(f"skipped images: {skipped}")
    print(f"num labels    : {len(palette)}")


if __name__ == "__main__":
    orig_densepose_dir = "/path/zalando-hd-resized/test/image-densepose"
    dump_dir = "/path/test/densepose_dumps"
    output_json = "/path/test/label_palette.json"

    extract_palette(
	orig_densepose_dir=orig_densepose_dir,
	dump_dir=dump_dir,
	output_json=output_json,
	max_images=100
    )
