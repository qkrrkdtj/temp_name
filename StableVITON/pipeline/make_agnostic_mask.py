import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


TARGET_SIZE = (768, 1024)  # (width, height)


def load_pose_json(pose_json_path: Path) -> np.ndarray:
    with open(pose_json_path, "r", encoding="utf-8") as f:
        pose_label = json.load(f)

    people = pose_label.get("people", [])
    if not people:
        raise ValueError(f"No person detected in pose json: {pose_json_path}")

    pose_data = np.array(people[0]["pose_keypoints_2d"], dtype=np.float32)
    pose_data = pose_data.reshape((-1, 3))[:, :2]
    return pose_data


def get_agnostic(im: Image.Image, im_parse: Image.Image, pose_data: np.ndarray) -> Image.Image:
    """
    CPDatasetTest.get_agnostic() 로직을 독립 스크립트로 옮긴 버전.
    """
    parse_array = np.array(im_parse)
    parse_head = (
        (parse_array == 4).astype(np.float32) +
        (parse_array == 13).astype(np.float32)
    )
    parse_lower = (
        (parse_array == 9).astype(np.float32) +
        (parse_array == 12).astype(np.float32) +
        (parse_array == 16).astype(np.float32) +
        (parse_array == 17).astype(np.float32) +
        (parse_array == 18).astype(np.float32) +
        (parse_array == 19).astype(np.float32)
    )

    agnostic = im.copy()
    agnostic_draw = ImageDraw.Draw(agnostic)

    pose_data = pose_data.copy()

    length_a = np.linalg.norm(pose_data[5] - pose_data[2])
    length_b = np.linalg.norm(pose_data[12] - pose_data[9])

    if length_a < 1e-6:
        length_a = 16.0

    if length_b >= 1e-6:
        point = (pose_data[9] + pose_data[12]) / 2
        pose_data[9] = point + (pose_data[9] - point) / length_b * length_a
        pose_data[12] = point + (pose_data[12] - point) / length_b * length_a

    r = int(length_a / 16) + 1

    # torso
    for i in [9, 12]:
        pointx, pointy = pose_data[i]
        agnostic_draw.ellipse(
            (pointx - r * 3, pointy - r * 6, pointx + r * 3, pointy + r * 6),
            "gray", "gray"
        )
    agnostic_draw.line([tuple(pose_data[i]) for i in [2, 9]], "gray", width=r * 6)
    agnostic_draw.line([tuple(pose_data[i]) for i in [5, 12]], "gray", width=r * 6)
    agnostic_draw.line([tuple(pose_data[i]) for i in [9, 12]], "gray", width=r * 12)
    agnostic_draw.polygon([tuple(pose_data[i]) for i in [2, 5, 12, 9]], "gray", "gray")

    # neck
    pointx, pointy = pose_data[1]
    agnostic_draw.rectangle(
        (pointx - r * 5, pointy - r * 9, pointx + r * 5, pointy),
        "gray", "gray"
    )

    # arms
    agnostic_draw.line([tuple(pose_data[i]) for i in [2, 5]], "gray", width=r * 12)
    for i in [2, 5]:
        pointx, pointy = pose_data[i]
        agnostic_draw.ellipse(
            (pointx - r * 5, pointy - r * 6, pointx + r * 5, pointy + r * 6),
            "gray", "gray"
        )

    for i in [3, 4, 6, 7]:
        if (
            (pose_data[i - 1, 0] == 0.0 and pose_data[i - 1, 1] == 0.0) or
            (pose_data[i, 0] == 0.0 and pose_data[i, 1] == 0.0)
        ):
            continue

        agnostic_draw.line([tuple(pose_data[j]) for j in [i - 1, i]], "gray", width=r * 10)
        pointx, pointy = pose_data[i]
        agnostic_draw.ellipse(
            (pointx - r * 5, pointy - r * 5, pointx + r * 5, pointy + r * 5),
            "gray", "gray"
        )

    # restore arm areas according to parse labels
    for parse_id, pose_ids in [(14, [5, 6, 7]), (15, [2, 3, 4])]:
        mask_arm = Image.new("L", im.size, "white")
        mask_arm_draw = ImageDraw.Draw(mask_arm)

        pointx, pointy = pose_data[pose_ids[0]]
        mask_arm_draw.ellipse(
            (pointx - r * 5, pointy - r * 6, pointx + r * 5, pointy + r * 6),
            "black", "black"
        )

        for i in pose_ids[1:]:
            if (
                (pose_data[i - 1, 0] == 0.0 and pose_data[i - 1, 1] == 0.0) or
                (pose_data[i, 0] == 0.0 and pose_data[i, 1] == 0.0)
            ):
                continue

            mask_arm_draw.line([tuple(pose_data[j]) for j in [i - 1, i]], "black", width=r * 10)
            pointx, pointy = pose_data[i]

            if i != pose_ids[-1]:
                mask_arm_draw.ellipse(
                    (pointx - r * 5, pointy - r * 5, pointx + r * 5, pointy + r * 5),
                    "black", "black"
                )

        mask_arm_draw.ellipse(
            (pointx - r * 4, pointy - r * 4, pointx + r * 4, pointy + r * 4),
            "black", "black"
        )

        parse_arm = (np.array(mask_arm) / 255.0) * (parse_array == parse_id).astype(np.float32)
        agnostic.paste(im, None, Image.fromarray(np.uint8(parse_arm * 255), "L"))

    # restore head and lower body
    agnostic.paste(im, None, Image.fromarray(np.uint8(parse_head * 255), "L"))
    agnostic.paste(im, None, Image.fromarray(np.uint8(parse_lower * 255), "L"))

    return agnostic


def build_mask_from_agnostic(agnostic_img: Image.Image) -> Image.Image:
    """
    agnostic RGB 이미지에서 회색으로 덮인 부분만 흰색(255)으로 저장.
    배경은 검정(0).
    """
    arr = np.array(agnostic_img.convert("RGB"))
    gray = np.array([128, 128, 128], dtype=np.uint8)

    mask = np.all(arr == gray, axis=2).astype(np.uint8) * 255
    return Image.fromarray(mask, mode="L")


def process_one(image_path: Path, parse_path: Path, pose_json_path: Path,
                agnostic_out_path: Path, mask_out_path: Path):
    person_img = Image.open(image_path).convert("RGB").resize(TARGET_SIZE, Image.LANCZOS)
    parse_img = Image.open(parse_path).resize(TARGET_SIZE, Image.NEAREST)
    pose_data = load_pose_json(pose_json_path)

    agnostic_img = get_agnostic(person_img, parse_img, pose_data)
    mask_img = build_mask_from_agnostic(agnostic_img)

    agnostic_out_path.parent.mkdir(parents=True, exist_ok=True)
    mask_out_path.parent.mkdir(parents=True, exist_ok=True)

    agnostic_img.save(agnostic_out_path, quality=100)
    mask_img.save(mask_out_path)

    print(f"[OK] agnostic: {agnostic_out_path.name}")
    print(f"[OK] mask    : {mask_out_path.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", type=str, required=True,
                        help="예: ./data/custom_test/test")
    parser.add_argument("--image_dir", type=str, default="image")
    parser.add_argument("--parse_dir", type=str, default="image-parse-v3")
    parser.add_argument("--pose_dir", type=str, default="openpose_json")
    parser.add_argument("--agnostic_dir", type=str, default="agnostic-v3.2")
    parser.add_argument("--mask_dir", type=str, default="agnostic-mask")
    parser.add_argument("--ext", type=str, default=".jpg",
                        help="person image 확장자, 기본 .jpg")
    args = parser.parse_args()

    data_root = Path(args.data_root)
    image_dir = data_root / args.image_dir
    parse_dir = data_root / args.parse_dir
    pose_dir = data_root / args.pose_dir
    agnostic_dir = data_root / args.agnostic_dir
    mask_dir = data_root / args.mask_dir

    image_paths = sorted(image_dir.glob(f"*{args.ext}"))
    if not image_paths:
        raise FileNotFoundError(f"No images found in: {image_dir}")

    for image_path in image_paths:
        stem = image_path.stem
        parse_path = parse_dir / f"{stem}.png"
        pose_json_path = pose_dir / f"{stem}_keypoints.json"

        if not parse_path.exists():
            print(f"[SKIP] parse not found: {parse_path}")
            continue
        if not pose_json_path.exists():
            print(f"[SKIP] pose json not found: {pose_json_path}")
            continue

        agnostic_out_path = agnostic_dir / f"{stem}.jpg"
        mask_out_path = mask_dir / f"{stem}_mask.png"

        try:
            process_one(
                image_path=image_path,
                parse_path=parse_path,
                pose_json_path=pose_json_path,
                agnostic_out_path=agnostic_out_path,
                mask_out_path=mask_out_path,
            )
        except Exception as e:
            print(f"[ERROR] {stem}: {e}")


if __name__ == "__main__":
    main()
