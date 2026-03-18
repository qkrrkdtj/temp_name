from pathlib import Path

STABLEVITON_ROOT = Path(r"C:\path\to\StableVITON")
PIPELINE_ROOT = STABLEVITON_ROOT / "pipeline"
RUNS_ROOT = STABLEVITON_ROOT / "runs"

OPENPOSE_ROOT = Path(r"C:\path\to\openpose")

DETECTRON2_ROOT = Path(r"C:\path\to\detectron2")
DENSEPOSE_ROOT = DETECTRON2_ROOT / "projects" / "DensePose"
DENSEPOSE_MODEL = "https://dl.fbaipublicfiles.com/densepose/densepose_rcnn_R_50_FPN_s1x/165712039/model_final_162be9.pkl"
DENSEPOSE_PALETTE_JSON = STABLEVITON_ROOT / "label_palette.json"

CONDA_ENV = "detectron2_dp"

SCHP_ROOT = Path(r"C:\path\to\Self-Correction-Human-Parsing")
SCHP_CONDA_ENV = "schp"