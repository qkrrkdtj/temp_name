# Backend API Documentation

## 🚀 FastAPI 백엔드 시스템

### 📋 개요
이 백엔드는 가상 피팅 웹 프론트엔드와 StableVITON 파이프라인을 연결하는 FastAPI 서버입니다.  
사용자 사진 업로드, 의류 선택 및 업로드, 의류 목록 조회, try-on 실행, 결과 이미지 반환 기능을 담당합니다.

기존의 단순 이미지 오버레이 방식이 아니라, StableVITON 전처리 및 추론 파이프라인을 실제로 실행하는 핵심 백엔드 서버입니다.

---

## 🏗️ 구조

```
backend/
├── main.py                    # FastAPI 메인 서버
├── requirements.txt           # Python 의존성 목록
├── README.md                  # 백엔드 설명 문서
├── api/                       # API 엔드포인트 관련 모듈
├── models/                    # 데이터 모델 정의
├── processing/                # 이미지 처리 및 전처리 로직
├── services/                  # 핵심 서비스 로직
└── uploads/                   # 업로드 파일 저장 폴더
    ├── person/                # 사용자 사진 저장
    └── cloth/                 # 의류 이미지 저장

```
각 폴더 및 파일 역할

- main.py: FastAPI 서버의 시작 파일입니다. 프론트엔드 요청을 받아 의류 목록 조회, 업로드 처리,
           가상 피팅 실행 및 결과 이미지 반환을 담당합니다.

- api/: API 엔드포인트를 기능별(업로드, 의류 목록, try-on 등)로 분리하여 관리하는 폴더입니다.

- models/: 요청/응답 데이터 구조 및 내부 데이터 모델을 정의합니다.

- processing/: 이미지 전처리, 파이프라인 입력 준비, 임시 처리 로직 등 이미지 처리 관련 코드를
               포함합니다.

- services/: 파일 저장, StableVITON 파이프라인 실행, 결과 이미지 탐색 등 핵심 비즈니스 로직을
             분리해 둔 폴더입니다.

- uploads/: 웹에서 업로드된 사용자 사진과 의류 이미지를 임시로 저장합니다. 
            (실제 이미지는 GitHub에 커밋하지 않고 폴더 구조만 유지합니다)

---
## 🔧 기술 스택

- **Python**  
  백엔드 서버 구현 언어

- **FastAPI**  
  가상 피팅 웹과 연결되는 API 서버 프레임워크

- **Uvicorn**  
  FastAPI 서버 실행용 ASGI 서버

- **StableVITON**  
  가상 피팅 생성 파이프라인

- **OpenPose**  
  사람 포즈 추출

- **SCHP**  
  사람 이미지 파싱

- **DensePose**  
  인체 밀집 포즈 추출

---

## 🚀 실행 방법

### 개발 환경
- **OS**: Windows
- **Language**: Python
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Frontend Dev Server**: Vite (`localhost:5173`)
- **Virtual Environment**: Anaconda / Conda environment
- **Pipeline Environment**: `clothmask_win`
- **Main Pipeline**: StableVITON
- **Related Tools**: OpenPose, SCHP, DensePose

# 서버 실행
```bash
cd backend
uvicorn main:app --reload
```
# Windows 환경에서 파이프라인 Python 지정
```bat
set PIPELINE_PYTHON=C:\ProgramData\anaconda3\envs\clothmask_win\python.exe
uvicorn main:app --reload
```

# 인코딩 문제 방지용 권장 실행 (Windows)
``` bat
chcp 65001
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PIPELINE_PYTHON=C:\ProgramData\anaconda3\envs\clothmask_win\python.exe
uvicorn main:app --reload
```

## 📡 API 엔드포인트

### 🏠 기본 엔드포인트
``` http
GET /
```
응답 예시: 
``` JSON
{
  "message": "server is running",
  "project_root": "...",
  "pipeline_script": "..."
}
```
#### 👕 의류 목록 조회
```http
GET /clothing/list?limit=3000
```
응답 예시:
``` JSON
{
  "files": ["000001.jpg", "000002.jpg"],
  "count": 2
}
```
#### 🧪 의류 경로 디버그 확인
```http
GET /clothing/debug
```
응답 예시:
```JSON
{
  "exists": true,
  "path": ".../StableVITON/data/custom/test/cloth",
  "count": 100,
  "files": ["000001.jpg", "000002.jpg"]
}
```

#### 📤 업로드
```http
POST /upload
Content-Type: multipart/form-data
```
폼 데이터 (Form Data):

- person_image: 사용자 사진 파일
- cloth_image: 의류 사진 파일

응답 예시:
``` JSON
{
  "message": "upload success",
  "person_image": ".../uploads/person/person_20260319_123456.jpg",
  "cloth_image": ".../uploads/cloth/cloth_20260319_123456.jpg",
  "person_filename": "person_20260319_123456.jpg",
  "cloth_filename": "cloth_20260319_123456.jpg"
}

```

### 🎭 가상 피팅 실행 (플레이스홀더)
``` http
POST /tryon
Content-Type: multipart/form-data
```
폼 데이터:
- person_image : 사용자 사진
- cloth_image : 업로드한 의류 이미지 (선택)
- cloth_id : 서버에 등록된 의류 파일명 (선택)
- cloth_image 또는 cloth_id 중 하나는 반드시 필요합니다.

응답 예시:
```JSON
{
  "message": "tryon pipeline executed successfully",
  "person_image": ".../uploads/person/person_20260319_123456.jpg",
  "cloth_image": ".../uploads/cloth/cloth_20260319_123456.jpg",
  "job_dir": ".../StableVITON/runs/job_20260319_123456",
  "result_image_path": ".../StableVITON/runs/job_20260319_123456/results/unpair/person_cloth.jpg",
  "result_image_url": "/static/runs/job_20260319_123456/results/unpair/person_cloth.jpg"
}
```

### 🖼️ Static 경로
의류 이미지
```text
/static/cloth/{filename}
```
결과 이미지
```text
/static/cloth/{filename}
```
프론트엔드는 이 경로를 통해 선택한 옷과 결과 이미지를 표시합니다.

---
### ⚙️ 동작 흐름

1. 사용자가 웹에서 사람 사진 업로드
2. 옷을 업로드하거나 기존 의류 목록에서 선택
3. 백엔드가 업로드 파일을 backend/uploads에 저장
4. 백엔드가 StableVITON 파이프라인 입력 폴더로 복사
5. StableVITON/pipeline/main_pipeline.py 실행
6. 최신 runs/job_* 폴더에서 결과 이미지 탐색
7. 결과 이미지 URL을 프론트엔드에 반환
8. 프론트엔드가 결과 이미지를 화면에 출력

---
### 📂 경로 구성 방식

이 서버는 개인 PC 절대경로 대신 상대경로 기반으로 동작하도록 구성했습니다.

기준:
- backend/main.py 위치를 기준으로 프로젝트 루트 계산
- StableVITON/pipeline
- StableVITON/data/custom/test/cloth
- StableVITON/runs
이 방식 덕분에 프로젝트 폴더 구조만 맞으면 다른 환경에서도 재사용하기 쉽습니다.

---
## 🚨 에러 처리

### 주요 에러 예시:
- 의류 파일을 찾을 수 없음
- main_pipeline.py를 찾을 수 없음
- 파이프라인 Python 실행 파일을 찾을 수 없음
- StableVITON 실행 중 오류 발생
- 결과 이미지가 생성되지 않음

### 에러 응답 형식
```Json
{
  "detail": {
    "message": "pipeline execution failed",
    "returncode": 1,
    "cmd": ["python", "..."],
    "stdout": "...",
    "stderr": "..."
  }
}
```

---
### 📌 정리

이 백엔드는 단순 업로드 서버가 아니라,
웹 프론트엔드와 StableVITON 파이프라인을 연결하는 실제 가상 피팅 서버입니다.

주요 역할:

- 사용자 입력 수집
- 의류 목록 제공
- 파이프라인 실행
- 결과 이미지 탐색 및 반환
- 정적 파일 제공
---