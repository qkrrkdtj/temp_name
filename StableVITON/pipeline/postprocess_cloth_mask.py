from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage


def keep_largest_component(binary: np.ndarray) -> np.ndarray:
    labeled, num = ndimage.label(binary)
    if num == 0:
        return binary

    sizes = ndimage.sum(binary, labeled, range(1, num + 1))
    largest_label = int(np.argmax(sizes)) + 1
    return labeled == largest_label


def fill_holes(binary: np.ndarray) -> np.ndarray:
    return ndimage.binary_fill_holes(binary)


def smooth_mask(binary: np.ndarray, close_iter=2, open_iter=1, dilate_iter=1) -> np.ndarray:
    binary = ndimage.binary_closing(binary, iterations=close_iter)
    binary = ndimage.binary_opening(binary, iterations=open_iter)
    binary = ndimage.binary_dilation(binary, iterations=dilate_iter)
    return binary


def postprocess_cloth_mask(mask_path: Path, min_area_ratio: float = 0.01):
    if not mask_path.exists():
        raise FileNotFoundError(f"cloth-mask 파일이 없습니다: {mask_path}")

    img = Image.open(mask_path).convert("L")
    arr = np.array(img, dtype=np.uint8)

    binary = arr > 127

    # 너무 작은 조각 제거 전에 전체 면적 체크
    h, w = binary.shape
    total_area = h * w

    binary = keep_largest_component(binary)
    binary = fill_holes(binary)
    binary = smooth_mask(binary, close_iter=2, open_iter=1, dilate_iter=1)
    binary = keep_largest_component(binary)

    white_area = int(binary.sum())
    area_ratio = white_area / float(total_area)

    if area_ratio < min_area_ratio:
        raise RuntimeError(
            f"cloth-mask 면적이 너무 작습니다: ratio={area_ratio:.4f}, path={mask_path}"
        )

    out = (binary.astype(np.uint8) * 255)
    Image.fromarray(out, mode="L").save(mask_path)

    print(f"[DONE] cloth-mask 후처리 완료: {mask_path}")
    print(f" - white area ratio: {area_ratio:.4f}")