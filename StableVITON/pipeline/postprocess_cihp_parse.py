from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage


def remove_small_components_per_label(label_map: np.ndarray, min_pixels: int = 40) -> np.ndarray:
    out = label_map.copy()
    labels = np.unique(label_map)

    for lbl in labels:
        if lbl == 0:
            continue  # 배경은 건드리지 않음

        mask = (label_map == lbl)
        labeled, num = ndimage.label(mask)
        if num == 0:
            continue

        sizes = ndimage.sum(mask, labeled, range(1, num + 1))
        sizes = np.asarray(sizes)

        for comp_idx, size in enumerate(sizes, start=1):
            if size < min_pixels:
                out[labeled == comp_idx] = 0

    return out


def fill_small_holes_per_label(label_map: np.ndarray, max_hole_pixels: int = 60) -> np.ndarray:
    out = label_map.copy()
    labels = np.unique(label_map)

    for lbl in labels:
        if lbl == 0:
            continue

        mask = (out == lbl)
        filled = ndimage.binary_fill_holes(mask)
        holes = filled & (~mask)

        if not holes.any():
            continue

        hole_labeled, num = ndimage.label(holes)
        if num == 0:
            continue

        sizes = ndimage.sum(holes, hole_labeled, range(1, num + 1))
        sizes = np.asarray(sizes)

        for comp_idx, size in enumerate(sizes, start=1):
            if size <= max_hole_pixels:
                out[hole_labeled == comp_idx] = lbl

    return out


def postprocess_cihp_parse(parse_path: Path, min_pixels: int = 40, max_hole_pixels: int = 60):
    if not parse_path.exists():
        raise FileNotFoundError(f"CIHP parse 파일이 없습니다: {parse_path}")

    img = Image.open(parse_path)
    arr = np.array(img, dtype=np.uint8)

    if arr.ndim == 3:
        arr = arr[:, :, 0]

    before = np.unique(arr)

    out = arr.copy()
    out = remove_small_components_per_label(out, min_pixels=min_pixels)
    out = fill_small_holes_per_label(out, max_hole_pixels=max_hole_pixels)

    Image.fromarray(out, mode="L").save(parse_path)

    after = np.unique(out)

    print(f"[DONE] CIHP parse 후처리 완료: {parse_path}")
    print(f" - labels before: {before.tolist()}")
    print(f" - labels after : {after.tolist()}")