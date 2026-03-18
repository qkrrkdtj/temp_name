# OpenPose

## 1. 개요

이 폴더는 StableVITON 전처리 과정에서 사용하는 OpenPose 환경에 대한 설명을 정리한 폴더입니다.

본 프로젝트에서는 사람 이미지에서 pose keypoint 정보를 추출하기 위해 OpenPose를 사용했습니다.

이 저장소에는 OpenPose 원본 코드를 포함하지 않았으며, 별도로 설치한 후 사용했습니다.

---

## 2. 역할

OpenPose는 사람 이미지에서 신체 keypoint를 추출하여 StableVITON 전처리 과정에서 사용하는 pose 정보를 생성하는 데 사용했습니다.

본 프로젝트에서는 입력된 사람 이미지 1장에 대해 OpenPose를 실행하고, 생성된 pose 결과를 이후 전처리 및 추론 과정에 사용했습니다.

---

## 3. 사용 환경

- Windows
- OpenPose 빌드 버전 사용
- `OpenPoseDemo.exe` 실행 방식 사용

본 프로젝트의 파이프라인에서는 OpenPose를 WSL이 아닌 **Windows 환경에서 직접 실행**하도록 구성했습니다.

---

## 4. 필요한 구성

OpenPose를 사용하기 위해 아래 항목이 필요합니다.

- `bin/OpenPoseDemo.exe`
- `models/`

즉, OpenPose 실행 파일과 모델 파일이 모두 준비되어 있어야 합니다.

---

## 5. 프로젝트 내 사용 목적

StableVITON은 사람의 자세 정보를 반영하기 위해 pose 입력이 필요합니다.

이를 위해 본 프로젝트에서는 OpenPose를 사용하여 사람 이미지의 pose keypoint를 추출하고, 해당 결과를 전처리 파이프라인에서 활용했습니다.

---

## 6. 실행 방식

OpenPose는 파이프라인 내부의 `run_openpose.py`를 통해 호출합니다.

즉, 사용자는 일반적으로 OpenPose를 직접 실행하기보다, 메인 파이프라인 실행 시 자동으로 OpenPose가 실행되도록 사용했습니다.

실행 흐름은 다음과 같습니다.

1. 사람 이미지 준비
2. `run_openpose.py` 실행
3. OpenPose keypoint 결과 생성
4. 이후 파이프라인 단계에서 사용

---

## 7. 경로 설정

OpenPose 경로는 `StableVITON/pipeline/config.py`에서 설정합니다.

예시:

```python
OPENPOSE_ROOT = Path(r"C:\path\to\openpose")
```