# Detectron2 / DensePose

## 1. 개요

이 폴더는 StableVITON 전처리 과정에서 사용하는 DensePose 생성 과정을 정리한 폴더입니다.

본 프로젝트에서는 Detectron2와 DensePose를 이용해 사람 이미지에서 DensePose 결과를 추출한 뒤, StableVITON에서 사용할 수 있는 RGB densepose 이미지로 변환했습니다.

이 저장소에는 Detectron2 원본 전체를 포함하지 않았으며, 별도로 설치한 후 사용했습니다.

---

## 2. 역할

DensePose는 사람 이미지의 신체 부위 정보를 추출하여 StableVITON 추론에 필요한 densepose 입력 이미지를 생성하는 데 사용했습니다.

본 프로젝트에서는 다음 세 단계로 densepose 이미지를 생성했습니다.

1. DensePose inference 결과를 `dump` 파일로 저장
2. VITONHD 학습 시 사용한 DensePose를 기반으로 palette 추출
3. dump 파일을 읽어 RGB palette 기반 densepose 이미지로 렌더링

---

## 3. 실행 환경

- WSL Ubuntu
- Conda 환경 사용
- 환경 이름 예시: `detectron2_dp`

---

## 4. 사용한 코드

DensePose 생성에는 아래 두 스크립트를 사용했습니다.

- `batch_densepose_dump.py`
- `palette_to_densepose.py`
- `render_densepose_from_palette_sample.py`

### 4-1. `batch_densepose_dump.py`
입력 이미지 폴더의 모든 이미지에 대해 DensePose dump 파일을 생성하는 스크립트입니다.

입력:
- 사람 이미지 폴더

출력:
- `*_densepose_dump.pkl` 파일들

### 4-2. `palette_to_densepose.py`
기존 DensePose로부터 추출한 `*_densepose_dump.pkl` 파일들과 기존 DensePose 이미지를 비교하여 `label_palette.json`을 생성하는 스크립트입니다.

입력:
- 기존 이미지의 DensePose
- 기존 이미지의 DensePose로부터 추출한 `*_densepose_dump.pkl`

출력:
- `label_palette.json`

### 4-3. `render_densepose_from_palette_sample.py`
생성된 dump 파일을 읽어, 가장 적절한 person instance를 선택한 뒤 label을 RGB palette로 변환하여 최종 densepose 이미지를 생성하는 스크립트입니다.

입력:
- DensePose dump 폴더
- 원본 사람 이미지 폴더
- `label_palette.json`

출력:
- 최종 densepose 이미지 폴더

---

## 5. 진행 과정

DensePose 생성 과정은 아래와 같습니다.

1. 사람 이미지에 대해 DensePose inference 수행
2. 결과를 dump 파일로 저장
3. dump 파일에서 가장 적절한 사람 instance 선택
4. DensePose part label 추출
5. label 값을 RGB palette로 매핑
6. StableVITON 전처리에 사용할 densepose 이미지로 저장

---

## 6. 경로 수정 후 실행 방법

스크립트 내부에는 작성 당시 사용한 절대경로가 들어 있으므로, 실행 전에 반드시 자신의 환경에 맞게 수정해야 합니다.

### 6-1. `batch_densepose_dump.py`에서 수정할 경로

아래 항목들을 자신의 환경에 맞게 수정합니다.

- `DETECTRON2_PATH`
- `DENSEPOSE_PATH`
- `CONFIG_PATH`
- `MODEL_PATH`
- `APPLY_NET_PATH`

이 스크립트는 실행 시 인자로 입력 이미지 폴더와 출력 dump 폴더를 받습니다.

실행 예시:

```bash
python batch_densepose_dump.py /path/to/image_dir /path/to/dump_dir
```

### 6-2 'render_densepose_from_palette_sample.py'에서 수정할 경로

스크립트 하단의 아래 변수들을 자신의 환경에 맞게 수정합니다.
- dump_dir
- ref_image_dir
- palette_json
- out_dir

필요한 경우 상단의 아래 경로도 수정합니다.
- sys.path.insert(... detectron2 경로 ...)
- sys.path.insert(... DensePose 경로 ...)

실행 예시:
```bash
python render_densepose_from_palette_sample.py
```
---

## 7. 생성 결과
최종적으로 아래 두 종류의 결과가 생성됩니다.

### 7-1 DensePose dump
- *_densepose_dump.pkl

### 7-2 DensePose RGB 이미지
- image-densepose/*.jpg

---

## 8. 참고 사항
- Detectron2 / DensePose 원본 코드는 이 저장소에 포함하지 않았습니다.
- 실제 실행 전 별도 설치가 필요합니다.
- 경로는 사용자 환경에 맞게 반드시 수정해야 합니다.
- palette 파일로는 label_palette.json을 사용했습니다.
