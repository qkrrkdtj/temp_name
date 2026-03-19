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
