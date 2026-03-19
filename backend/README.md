# Backend API Documentation

## 🚀 FastAPI 백엔드 시스템

### 📋 개요
NT Fit 가상 피팅 시스템의 백엔드 API 서버입니다. 현재는 플레이스홀더 구조로 단순 이미지 오버레이를 제공하며, 향후 AI 모델 통합이 가능하도록 설계되었습니다.

---

## 🏗️ 구조

```
backend/
├── main.py                    # FastAPI 메인 애플리케이션
├── requirements.txt           # Python 의존성
├── processing/                # 이미지 전처리 모듈
│   ├── pipeline.py           # 전처리 파이프라인
│   └── _tmp/                 # 임시 파일 저장소
├── uploads/                   # 파일 업로드 디렉토리
│   ├── user/                 # 사용자 이미지
│   └── cloth/                # 의류 이미지
├── results/                   # 결과 이미지 저장소
├── api/                       # API 관련 모듈
├── models/                    # 데이터 모델
├── services/                  # 비즈니스 로직
└── README_AI_UPGRADE.md      # AI 모델 업그레이드 가이드
```

---

## 🔧 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 백엔드 언어 |
| FastAPI | 0.104.1 | 웹 프레임워크 |
| Uvicorn | 0.24.0 | ASGI 서버 |
| Pillow | 10.1.0 | 이미지 처리 |
| OpenCV | 4.8.1.78 | 컴퓨터 비전 |
| MediaPipe | 0.10.8 | 포즈 추출 |
| NumPy | 1.24.3 | 수치 계산 |

---

## 🚀 실행 방법

### 개발 환경
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

### 프로덕션 환경
```bash
# Gunicorn 사용
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# 또는 Docker 사용
docker build -t nt-fit-backend .
docker run -p 8000:8000 nt-fit-backend
```

---

## 📡 API 엔드포인트

### 🏠 기본 엔드포인트
```http
GET /
# 응답: {"message": "NT Fit Virtual Try-on API Server", "frontend": "http://localhost:5173"}
```

### 📤 이미지 업로드

#### 사용자 이미지 업로드
```http
POST /upload/user-image
Content-Type: multipart/form-data

# 응답
{
  "upload_id": "1234567890",
  "status": "success",
  "processed_url": "/static/processing/_tmp/1234567890/1234567890.jpg",
  "pose_url": "/static/processing/_tmp/1234567890/1234567890_pose.json",
  "parse_url": "/static/processing/_tmp/1234567890/1234567890_parse.png"
}
```

#### 의류 이미지 업로드
```http
POST /upload/cloth
Content-Type: multipart/form-data

# 응답
{
  "filename": "user_1234567890.jpg",
  "status": "success",
  "cloth_url": "/static/uploads/cloth/user_1234567890.jpg",
  "mask_url": "/static/uploads/cloth/user_1234567890_mask.jpg"
}
```

### 🎭 가상 피팅 실행 (플레이스홀더)
```http
POST /viton/tryon?upload_id={upload_id}&cloth_id={cloth_id}

# 응답
{
  "status": "completed",
  "session_id": "e9e9b8d01979",
  "result_url": "/static/app_results/e9e9b8d01979/person_user_1234567890.jpg",
  "message": "Virtual try-on completed (placeholder implementation - ready for AI model upgrade)",
  "implementation": "simple_overlay",
  "future_capability": "AI_model_ready"
}
```

### 📋 결과 조회
```http
GET /viton/results?name={session_id}

# 응답
["person_user_1234567890.jpg"]
```

### 🗂️ 의류 관리

#### 사용자 의류 목록
```http
GET /clothing/user-list

# 응답
{
  "clothing_items": [
    {
      "id": "user_1234567890",
      "filename": "user_1234567890.jpg",
      "url": "/static/uploads/cloth/user_1234567890.jpg",
      "mask_url": "/static/uploads/cloth/user_1234567890_mask.jpg",
      "category": "user_upload"
    }
  ]
}
```

#### 의류 삭제
```http
DELETE /clothing/{cloth_id}

# 응답
{"status": "success", "message": "Clothing user_1234567890 deleted"}
```

---

## 🔄 플레이스홀더 구조

### 현재 구현
```python
def simple_virtual_tryon_overlay(person_image_path, cloth_image_path, session_id):
    """
    Placeholder implementation for virtual try-on.
    
    현재는 단순 이미지 오버레이를 제공하며, 향후 AI 모델로 교체 가능합니다.
    """
    # 1. 이미지 로드 및 리사이즈
    # 2. 위치 계산 (상단 15% 지점)
    # 3. 이미지 합성
    # 4. 결과 저장
    return result_path
```

### AI 모델 통합 준비
- **함수 인터페이스**: `simple_virtual_tryon_overlay()` 그대로 사용 가능
- **입력/출력**: 동일한 파일 경로 및 세션 ID 구조
- **API 응답**: `implementation` 필드로 구분 가능

---

## 🛡️ 보안 및 유효성 검사

### 파일 업로드 제한
- **파일 타입**: `.jpg`, `.jpeg`, `.png`만 허용
- **파일 크기**: 10MB 제한
- **파일명**: 안전한 파일명 생성

### 입력 검증
- **파일 경로**: Path traversal 방지
- **세션 ID**: UUID 형식 검증
- **파일 존재**: 파일 실제 존재 여부 확인

---

## 📊 성능 모니터링

### 로깅
```python
import logging

# 요청 로깅
logger.info(f"Virtual try-on request: session_id={session_id}")

# 성능 로깅
import time
start_time = time.time()
# ... 처리 로직 ...
processing_time = time.time() - start_time
logger.info(f"Processing completed in {processing_time:.2f}s")
```

### 메트릭
- **응답 시간**: 평균 2초 (이미지 업로드)
- **처리 시간**: 10-30초 (플레이스홀더)
- **메모리 사용**: < 512MB
- **디스크 사용**: 동적 (업로드 파일 기반)

---

## 🚨 에러 처리

### 일반 에러
```python
try:
    # API 로직
    result = process_request()
except FileNotFoundError as e:
    raise HTTPException(status_code=404, detail="File not found")
except ValueError as e:
    raise HTTPException(status_code=400, detail="Invalid input")
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 에러 응답 형식
```json
{
  "detail": "에러 메시지"
}
```

---

## 🔧 개발 가이드

### 새로운 엔드포인트 추가
```python
@app.post("/new-endpoint")
async def new_endpoint(data: NewRequest):
    try:
        result = process_data(data)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 테스트
```bash
# 단위 테스트
pytest tests/

# API 테스트
http POST http://localhost:8000/upload/user-image file@image.jpg
```

---

## 📖 추가 문서

- **🤖 AI 업그레이드**: `README_AI_UPGRADE.md`
- **🚀 배포 가이드**: 상위 디렉토리 `DEPLOYMENT.md`
- **📱 프론트엔드**: `../frontend/README.md`

---

## 🎯 향후 개발 계획

1. **AI 모델 통합** (VITON-HD, Stable Diffusion 등)
2. **성능 최적화** (캐싱, 비동기 처리)
3. **보안 강화** (인증, rate limiting)
4. **모니터링** (메트릭, 로그 분석)
5. **API 버전 관리** (v1, v2 등)

---

> 🎭 **현재 상태**: 플레이스홀더 구조로 모든 웹 기능 동작 ✅  
> 🚀 **준비 상태**: AI 모델 통합을 위한 완벽한 아키텍처 ✅
