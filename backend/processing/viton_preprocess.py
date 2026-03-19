"""
사용자 업로드 이미지를 VITON-HD test.py 입력 형식으로 변환합니다.
- 포즈: MediaPipe Pose → OpenPose JSON + 렌더 이미지
- 파싱: 포즈 기반 최소 파싱 맵 (상의·팔 등)
- 의류 마스크: 옷 이미지에 대해 rembg 또는 기존 마스크 사용
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

# MediaPipe → OpenPose 18 keypoints (0-17) 매핑
# OpenPose: 0=Nose, 1=Neck, 2=RShoulder, 3=RElbow, 4=RWrist, 5=LShoulder, 6=LElbow, 7=LWrist,
#           8=MidHip, 9=RHip, 10=RKnee, 11=RAnkle, 12=LHip, 13=LKnee, 14=LAnkle, 15=REye, 16=LEye, 17=REar, 18=LEar
MEDIAPIPE_TO_OPENPOSE_18: List[int] = [
    0,   # 0 Nose <- mp 0
    0,   # 1 Neck <- (11+12)/2 → 별도 계산
    12,  # 2 RShoulder
    14,  # 3 RElbow
    16,  # 4 RWrist
    11,  # 5 LShoulder
    13,  # 6 LElbow
    15,  # 7 LWrist
    0,   # 8 MidHip <- (23+24)/2
    24,  # 9 RHip
    26,  # 10 RKnee
    28,  # 11 RAnkle
    23,  # 12 LHip
    25,  # 13 LKnee
    27,  # 14 LAnkle
    5,   # 15 REye (mp 4=right eye inner, 5=right eye)
    2,   # 16 LEye
    8,   # 17 REar
    7,   # 18 LEar
]

VITON_SIZE = (768, 1024)  # width, height (load_width, load_height)


def _get_pose_keypoints_2d(landmarks, width: int, height: int) -> np.ndarray:
    """MediaPipe landmark → OpenPose 형식 (18, 3) 배열. x,y는 픽셀 좌표."""
    # MediaPipe: x,y 정규화 [0,1], z 상대적
    out = np.zeros((19, 3), dtype=np.float32)  # 0~18
    for op_idx in range(19):
        if op_idx == 1:  # Neck
            if landmarks[11].visibility > 0.5 and landmarks[12].visibility > 0.5:
                x = (landmarks[11].x + landmarks[12].x) / 2
                y = (landmarks[11].y + landmarks[12].y) / 2
                c = 1.0
            else:
                x, y, c = 0.0, 0.0, 0.0
        elif op_idx == 8:  # MidHip
            if landmarks[23].visibility > 0.5 and landmarks[24].visibility > 0.5:
                x = (landmarks[23].x + landmarks[24].x) / 2
                y = (landmarks[23].y + landmarks[24].y) / 2
                c = 1.0
            else:
                x, y, c = 0.0, 0.0, 0.0
        else:
            mp_idx = MEDIAPIPE_TO_OPENPOSE_18[op_idx] if op_idx < len(MEDIAPIPE_TO_OPENPOSE_18) else 0
            lm = landmarks[mp_idx]
            x, y = lm.x, lm.y
            c = lm.visibility if hasattr(lm, 'visibility') else 1.0
        out[op_idx, 0] = x * width
        out[op_idx, 1] = y * height
        out[op_idx, 2] = c
    return out[:18]  # OpenPose 18 keypoints


def mediapipe_pose_to_openpose(
    image_path: Path,
    out_json_path: Path,
    out_rendered_path: Path,
    size: Tuple[int, int] = VITON_SIZE,
) -> bool:
    """
    이미지에서 MediaPipe로 포즈 추정 후 OpenPose 형식 JSON과 렌더 이미지를 저장합니다.
    size: (width, height) = (768, 1024)
    개선: 더 나은 에러 처리와 로깅 추가
    """
    try:
        import mediapipe as mp
    except ImportError:
        print("Warning: mediapipe not installed. Pose estimation will fail.")
        return False

    try:
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Error: Cannot read image {image_path}")
            return False
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        
        # VITON 해상도로 리사이즈 후 포즈 추정 (일관된 좌표를 위해)
        scale_w = size[0] / w
        scale_h = size[1] / h
        scale = min(scale_w, scale_h, 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img_rgb = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # 패딩하여 768x1024
        target_w, target_h = size[0], size[1]
        pad_w = target_w - img_rgb.shape[1]
        pad_h = target_h - img_rgb.shape[0]
        top, left = pad_h // 2, pad_w // 2
        padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        padded.fill(255)
        padded[top : top + img_rgb.shape[0], left : left + img_rgb.shape[1]] = img_rgb
        img_rgb = padded
        w, h = target_w, target_h

        mp_pose = mp.solutions.pose
        # 더 나은 포즈 추정 파라미터
        with mp_pose.Pose(
            static_image_mode=True, 
            model_complexity=2,  # 더 정확한 모델
            min_detection_confidence=0.3,  # 더 낮은 임계값
            min_tracking_confidence=0.3
        ) as pose:
            results = pose.process(img_rgb)

        if not results.pose_landmarks:
            print(f"Warning: No pose landmarks detected in {image_path}")
            # 빈 키포인트로 저장 (실패 시에도 파일은 있게)
            keypoints = np.zeros((18, 3), dtype=np.float32)
        else:
            keypoints = _get_pose_keypoints_2d(results.pose_landmarks.landmark, w, h)
            # 키포인트 유효성 검사
            valid_points = np.sum(keypoints[:, 2] > 0.3)
            if valid_points < 5:  # 유효한 점이 너무 적으면 경고
                print(f"Warning: Only {valid_points} valid keypoints detected in {image_path}")

        # OpenPose JSON: people[0].pose_keypoints_2d = [x1,y1,c1, x2,y2,c2, ...]
        flat = keypoints.flatten().tolist()
        openpose_obj = {"people": [{"pose_keypoints_2d": flat}]}
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump(openpose_obj, f, indent=2)

        # 렌더 이미지: 스켈레톤 그리기 (BGR)
        # 연결: 1-2, 1-5, 2-3, 3-4, 5-6, 6-7, 1-8, 8-9, 9-10, 10-11, 8-12, 12-13, 13-14, 2-9, 5-12
        skeleton = [
            (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
            (1, 8), (8, 9), (9, 10), (10, 11), (8, 12), (12, 13), (13, 14),
            (2, 9), (5, 12),
            (0, 15), (0, 16), (15, 17), (16, 18),
        ]
        rendered = img_rgb.copy()
        for i, j in skeleton:
            if i >= keypoints.shape[0] or j >= keypoints.shape[0]:
                continue
            if keypoints[i, 2] > 0.3 and keypoints[j, 2] > 0.3:
                x1, y1 = int(keypoints[i, 0]), int(keypoints[i, 1])
                x2, y2 = int(keypoints[j, 0]), int(keypoints[j, 1])
                cv2.line(rendered, (x1, y1), (x2, y2), (0, 255, 0), 2)
        for i in range(keypoints.shape[0]):
            if keypoints[i, 2] > 0.3:
                x, y = int(keypoints[i, 0]), int(keypoints[i, 1])
                cv2.circle(rendered, (x, y), 4, (0, 0, 255), -1)
        out_rendered_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_rendered_path), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
        return True
    except Exception as e:
        print(f"Error in pose estimation for {image_path}: {e}")
        return False


def create_minimal_parse_from_pose(
    pose_json_path: Path,
    width: int,
    height: int,
) -> Image.Image:
    """
    OpenPose JSON에서 키포인트를 읽어 VITON 형식의 최소 파싱 맵(0~19 라벨)을 생성합니다.
    상의(5,6,7), 왼팔(14), 오른팔(15), 하의(9,12) 등만 채우고 나머지는 0(배경)으로 둡니다.
    개선: 더 나은 신체 부위 추정과 오류 처리
    """
    try:
        with open(pose_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        people = data.get("people", [])
        if not people:
            print(f"Warning: No people found in pose data {pose_json_path}")
            arr = np.zeros((height, width), dtype=np.uint8)
            return Image.fromarray(arr, mode="L")

        flat = people[0].get("pose_keypoints_2d", [])
        if len(flat) < 54:  # 18 points * 3 coordinates
            print(f"Warning: Insufficient keypoints in {pose_json_path}")
            arr = np.zeros((height, width), dtype=np.uint8)
            return Image.fromarray(arr, mode="L")
            
        kp = np.array(flat, dtype=np.float32).reshape(-1, 3)[:18]
        # 유효한 점만 사용
        pts = []
        for i in range(18):
            if kp[i, 2] > 0.2:
                pts.append((int(kp[i, 0]), int(kp[i, 1])))

        parse = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(parse)
        r = 12

        # 상의 영역: 5(LShoulder), 2(RShoulder), 9(RHip), 12(LHip) → 5,6,7
        upper_idx = [5, 2, 9, 12]
        if all(kp[i, 2] > 0.2 for i in upper_idx):
            # 더 부드러운 상의 영역 생성
            poly = [tuple(kp[i, :2].astype(int)) for i in upper_idx]
            # 목 부분 추가 (1번 Neck)
            if kp[1, 2] > 0.2:
                neck = tuple(kp[1, :2].astype(int))
                # 목을 상의 영역에 포함
                extended_poly = poly + [neck]
                draw.polygon(extended_poly, fill=5)
            else:
                draw.polygon(poly, fill=5)
        else:
            # 일부 키포인트만 있을 때 대체 처리
            valid_shoulders = [i for i in [5, 2] if kp[i, 2] > 0.2]
            valid_hips = [i for i in [9, 12] if kp[i, 2] > 0.2]
            if len(valid_shoulders) >= 2 and len(valid_hips) >= 1:
                poly = [tuple(kp[i, :2].astype(int)) for i in valid_shoulders + valid_hips[:2]]
                draw.polygon(poly, fill=5)
                
        # 왼팔 14: 5-6-7
        for (i, j) in [(5, 6), (6, 7)]:
            if kp[i, 2] > 0.2 and kp[j, 2] > 0.2:
                draw.line([tuple(kp[i, :2].astype(int)), tuple(kp[j, :2].astype(int))], fill=14, width=r * 2)
                draw.ellipse((kp[j, 0] - r, kp[j, 1] - r, kp[j, 0] + r, kp[j, 1] + r), fill=14)
                
        # 오른팔 15: 2-3-4
        for (i, j) in [(2, 3), (3, 4)]:
            if kp[i, 2] > 0.2 and kp[j, 2] > 0.2:
                draw.line([tuple(kp[i, :2].astype(int)), tuple(kp[j, :2].astype(int))], fill=15, width=r * 2)
                draw.ellipse((kp[j, 0] - r, kp[j, 1] - r, kp[j, 0] + r, kp[j, 1] + r), fill=15)
                
        # 하의 9,12: 8-9-10-11, 8-12-13-14
        lower_idx = [8, 9, 10, 11, 12, 13, 14]
        if kp[8, 2] > 0.2:
            # 오른쪽 다리
            if kp[9, 2] > 0.2:
                draw.line([tuple(kp[8, :2].astype(int)), tuple(kp[9, :2].astype(int))], fill=9, width=r * 2)
                if kp[10, 2] > 0.2:
                    draw.line([tuple(kp[9, :2].astype(int)), tuple(kp[10, :2].astype(int))], fill=9, width=r * 2)
                    if kp[11, 2] > 0.2:
                        draw.ellipse((kp[11, 0] - r, kp[11, 1] - r, kp[11, 0] + r, kp[11, 1] + r), fill=9)
            # 왼쪽 다리
            if kp[12, 2] > 0.2:
                draw.line([tuple(kp[8, :2].astype(int)), tuple(kp[12, :2].astype(int))], fill=12, width=r * 2)
                if kp[13, 2] > 0.2:
                    draw.line([tuple(kp[12, :2].astype(int)), tuple(kp[13, :2].astype(int))], fill=12, width=r * 2)
                    if kp[14, 2] > 0.2:
                        draw.ellipse((kp[14, 0] - r, kp[14, 1] - r, kp[14, 0] + r, kp[14, 1] + r), fill=12)
                        
        # 얼굴/머리 4, 13
        if kp[0, 2] > 0.2:
            draw.ellipse((kp[0, 0] - r * 3, kp[0, 1] - r * 3, kp[0, 0] + r * 3, kp[0, 1] + r * 3), fill=4)
            
        return parse
    except Exception as e:
        print(f"Error creating parse map from {pose_json_path}: {e}")
        # 실패 시 빈 파싱 맵 반환
        arr = np.zeros((height, width), dtype=np.uint8)
        return Image.fromarray(arr, mode="L")


def generate_cloth_mask(cloth_image_path: Path, out_mask_path: Path) -> bool:
    """의류 이미지에서 배경 제거 후 마스크(그레이스케일, 0/255) 저장.
    개선: 더 나은 오류 처리와 대체 방법 제공"""
    import io
    try:
        from rembg import remove
    except ImportError:
        print("Warning: rembg not installed. Using simple threshold method for cloth mask.")
        # 간단한 임계값 방식으로 대체
        try:
            with Image.open(cloth_image_path) as img:
                img = img.convert("RGB")
                # 간단한 배경 제거: 밝은 영역을 배경으로 간주
                img_array = np.array(img)
                # 그레이스케일 변환
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                # Otsu의 임계값으로 이진화
                _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                # 노이즈 제거
                kernel = np.ones((3,3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                out_mask_path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(mask).save(out_mask_path)
                return True
        except Exception as e:
            print(f"Error in simple cloth mask generation: {e}")
            return False
    
    try:
        with open(cloth_image_path, "rb") as f:
            img_bytes = f.read()
        out_bytes = remove(img_bytes)
        mask_im = Image.open(io.BytesIO(out_bytes)).convert("RGBA")
        arr = np.array(mask_im)
        alpha = arr[:, :, 3]
        gray = (alpha >= 128).astype(np.uint8) * 255
        out_mask_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(gray).save(out_mask_path)
        return True
    except Exception as e:
        print(f"Error in rembg cloth mask generation: {e}")
        # rembg 실패 시 간단한 방법으로 대체
        try:
            with Image.open(cloth_image_path) as img:
                img = img.convert("RGB")
                img_array = np.array(img)
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                kernel = np.ones((3,3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                out_mask_path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(mask).save(out_mask_path)
                return True
        except Exception as e2:
            print(f"Error in fallback cloth mask generation: {e2}")
            return False


def build_viton_input_dir(
    person_image_path: Path,
    cloth_image_path: Path,
    cloth_mask_path: Path | None,
    session_id: str,
    out_base_dir: Path,
    person_filename: str = "person.jpg",
    cloth_filename: str = "cloth.jpg",
) -> Path:
    """
    VITON test 디렉터리 구조를 만듭니다.
    - image/{person_filename}
    - image-parse/{person_stem}.png
    - openpose-img/{person_stem}_rendered.png
    - openpose-json/{person_stem}_keypoints.json
    - cloth/{cloth_filename}
    - cloth-mask/{cloth_filename}
    - test_pairs.txt: 한 줄 "person_name cloth_name"
    person_image_path: 768x1024로 리사이즈되어 복사됩니다.
    """
    import io
    out_base_dir = Path(out_base_dir)
    # VITON data_path = dataset_dir / dataset_mode → .../test/image 등
    viton_test = out_base_dir / "viton_input" / session_id
    test_dir = viton_test / "test"
    dirs = [
        test_dir / "image",
        test_dir / "image-parse",
        test_dir / "openpose-img",
        test_dir / "openpose-json",
        test_dir / "cloth",
        test_dir / "cloth-mask",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # 인물 이미지: 768x1024로 리사이즈 후 저장
    person_stem = Path(person_filename).stem
    person_final = test_dir / "image" / person_filename
    with Image.open(person_image_path) as im:
        im = im.convert("RGB")
        im = im.resize((VITON_SIZE[0], VITON_SIZE[1]), Image.Resampling.LANCZOS)
        im.save(person_final, quality=95)

    # 포즈 생성 (MediaPipe → OpenPose)
    pose_json = test_dir / "openpose-json" / f"{person_stem}_keypoints.json"
    pose_rendered = test_dir / "openpose-img" / f"{person_stem}_rendered.png"
    
    # 포즈 추정 성공 여부 확인
    pose_success = mediapipe_pose_to_openpose(person_final, pose_json, pose_rendered, size=VITON_SIZE)
    if not pose_success:
        print(f"Warning: Pose estimation failed for {person_final}. Creating empty keypoints file.")
        # 빈 키포인트 파일 생성 (VITON 실행을 위해)
        empty_keypoints = {
            "people": [{
                "pose_keypoints_2d": [0.0] * 54  # 18 points * 3 coordinates
            }]
        }
        pose_json.parent.mkdir(parents=True, exist_ok=True)
        with open(pose_json, "w", encoding="utf-8") as f:
            json.dump(empty_keypoints, f, indent=2)
        
        # 빈 렌더 이미지 생성
        empty_render = Image.new('RGB', VITON_SIZE, (255, 255, 255))
        pose_rendered.parent.mkdir(parents=True, exist_ok=True)
        empty_render.save(pose_rendered)

    # 파싱 생성
    parse_img = create_minimal_parse_from_pose(pose_json, VITON_SIZE[0], VITON_SIZE[1])
    parse_path = test_dir / "image-parse" / f"{person_stem}.png"
    parse_img.save(parse_path)

    # 의류 복사 (VITON 해상도에 맞게 리사이즈)
    cloth_final = test_dir / "cloth" / cloth_filename
    with Image.open(cloth_image_path) as c_im:
        c_im = c_im.convert("RGB")
        c_im = c_im.resize((VITON_SIZE[0], VITON_SIZE[1]), Image.Resampling.LANCZOS)
        c_im.save(cloth_final, quality=95)
    mask_final = test_dir / "cloth-mask" / cloth_filename
    mask_final.parent.mkdir(parents=True, exist_ok=True)
    if cloth_mask_path and cloth_mask_path.exists():
        with Image.open(cloth_mask_path) as m:
            m = m.convert("L").resize((VITON_SIZE[0], VITON_SIZE[1]), Image.Resampling.NEAREST)
            m.save(mask_final)
    else:
        # rembg로 마스크 생성, 실패 시 전체 영역 마스크로 대체 (FileNotFoundError 방지)
        if not generate_cloth_mask(cloth_final, mask_final):
            Image.fromarray(np.uint8(np.ones((VITON_SIZE[1], VITON_SIZE[0])) * 255)).save(mask_final)
    # 어떤 경로로 생성됐든 최종적으로 cloth-mask를 VITON 해상도로 강제 정규화
    with Image.open(mask_final) as m:
        m = m.convert("L").resize((VITON_SIZE[0], VITON_SIZE[1]), Image.Resampling.NEAREST)
        m.save(mask_final)

    # test_pairs.txt (dataset_dir 루트에 두기)
    pairs_file = viton_test / "test_pairs.txt"
    with open(pairs_file, "w", encoding="utf-8") as f:
        f.write(f"{person_filename} {cloth_filename}\n")

    return viton_test
