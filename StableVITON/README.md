# StableVITON Pipeline

## 1. 개요

이 폴더는 StableVITON 기반 가상 피팅 파이프라인을 실행하기 위한 코드입니다.

사람 이미지 1장과 의상 이미지 1장을 입력으로 받아 아래 과정을 순서대로 수행합니다.

1. 입력 이미지 정리
2. 768x1024 해상도 통일
3. 배경 제거 후 흰 배경 합성
4. OpenPose 실행
5. SCHP(Human Parsing) 실행
6. DensePose 실행
7. Cloth Mask 생성
8. Agnostic Mask 생성
9. StableVITON 추론용 dataset 구성
10. StableVITON inference 실행

최종적으로 가상 피팅 결과 이미지를 생성합니다.

---

## 2. 현재 사용 중인 파이프라인 파일

현재 메인 파이프라인에서 사용하는 파일은 아래와 같습니다.

- `main_pipeline.py`
- `config.py`
- `run_prepare_inputs.py`
- `run_openpose.py`
- `run_schp.py`
- `run_densepose.py`
- `run_cloth_mask.py`
- `run_make_agnostic_mask.py`
- `build_stableviton_dataset.py`
- `make_agnostic_mask.py`
- `postprocess_cloth_mask.py`

---

## 3. 실행 환경

이 파이프라인은 **Windows + WSL Ubuntu + Conda** 기준으로 구성했습니다.

### Windows 측
- OpenPose 실행
- 메인 파이프라인 실행
- carvekit 실행
- StableVITON inference 실행

### WSL 측
- SCHP 실행
- DensePose 실행

---

## 4. 폴더 구조 예시

프로젝트 루트는 아래와 같은 형태로 정리했습니다.

```text
project-root/
├─ StableVITON/
│  ├─ pipeline/
│  ├─ configs/
│  ├─ ckpts/
│  ├─ inference.py
│  └─ label_palette.json
├─ openpose/
├─ detectron2/
└─ Self-Correction-Human-Parsing/
```

---

## 5. 외부 프로젝트 준비
이 저장소에는 외부 프로젝트 원본 코드는 포함하지 않았습니다. 아래 프로젝트들은 별도로 준비해야 합니다.

### 5-1. OpenPose
Windows에서 실행 가능한 OpenPose 빌드가 필요합니다.

- bin/OpenPoseDemo.exe
- models/

### 5-2. Detectron2 / DensePose
WSL 환경에서 DensePose를 실행하기 위해 Detectron2와 DensePose가 필요합니다.

- detectron2
- detectron2/projects/DensePose

### 5-3. SCHP
WSL 환경에서 human parsing을 수행하기 위해 SCHP가 필요합니다.

- simple_extractor.py
- checkpoints/exp-schp-201908261155-lip.pth

---

## 6. config.py 설정
파이프라인 실행 전 config.py에서 경로를 반드시 수정해야 합니다.

- STABLEVITON_ROOT
- OPENPOSE_ROOT
- DETECTRON2_ROOT
- DENSEPOSE_ROOT
- SCHP_ROOT
- CONDA_ENV
- SCHP_CONDA_ENV

---

## 7. 입력 이미지 넣는 방법
입력 이미지는 아래 폴더에 넣습니다.

- 사람 이미지: pipeline/input_drop/person
- 의상 이미지: pipeline/input_drop/cloth

현재 파이프라인은 각 폴더에서 첫 번째 이미지 1장만 사용합니다.
```text
pipeline/
└─ input_drop/
   ├─ person/
   │  └─ user.jpg
   └─ cloth/
      └─ cloth.jpg
```
---

## 8. 실행 방법

python main_pipeline.py

파이프라인은 아래 순서로 동작합니다.

1. 입력 이미지 복사 및 이름 정리
2. 리사이즈
3. 배경 제거 및 흰 배경 합성
4. OpenPose 실행
5. SCHP 실행
6. DensePose 실행
7. Cloth Mask 생성
8. Agnostic Mask 생성
9. StableVITON용 dataset 생성
10. inference 실행
