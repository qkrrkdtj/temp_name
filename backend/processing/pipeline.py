from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from PIL import Image


@dataclass(frozen=True)
class PreprocessResult:
    input_path: Path
    processed_path: Path
    size: Tuple[int, int]


def preprocess_user_image(
    *,
    input_path: Path,
    out_dir: Path,
    max_size: int = 1024,
    out_format: str = "jpg",
) -> PreprocessResult:
    """
    사용자 업로드 이미지를 모델 파이프라인에 넣기 쉬운 형태로 정리합니다.
    - RGB 변환
    - 최대 변 길이를 max_size로 축소(비율 유지)
    - jpg로 저장(기본)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{input_path.stem}.{out_format}"

    with Image.open(input_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, max_size / max(w, h)) if max(w, h) else 1.0
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        im.save(out_path, quality=92, optimize=True)

    with Image.open(out_path) as out_im:
        size = out_im.size

    return PreprocessResult(input_path=input_path, processed_path=out_path, size=size)

