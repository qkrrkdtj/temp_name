import subprocess
import shutil
import time
from pathlib import Path
import sys

from config import SCHP_ROOT, SCHP_CONDA_ENV
from postprocess_cihp_parse import postprocess_cihp_parse


def to_wsl_path(win_path: Path) -> str:
    s = str(win_path).replace("\\", "/")
    drive = s[0].lower()
    rest = s[2:]
    return f"/mnt/{drive}{rest}"


def clear_dir(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def run_schp(paths):
    start_time = time.time()
    print("[TIME] SCHP 시작")

    image_dir = paths["image_dir"]
    parse_dir = paths["parse_dir"]

    schp_root_win = SCHP_ROOT
    schp_input_dir_win = schp_root_win / "input_for_pipeline"
    schp_output_dir_win = schp_root_win / "output_for_pipeline"

    clear_dir(schp_input_dir_win)
    clear_dir(schp_output_dir_win)

    try:
        copied = []
        for img_path in image_dir.iterdir():
            if img_path.is_file():
                dst = schp_input_dir_win / img_path.name
                shutil.copy2(img_path, dst)
                copied.append(dst)

        if not copied:
            raise FileNotFoundError(f"SCHP 입력 이미지가 없습니다: {image_dir}")

        if parse_dir.exists():
            shutil.rmtree(parse_dir)
        parse_dir.mkdir(parents=True, exist_ok=True)

        schp_root_wsl = to_wsl_path(schp_root_win)
        schp_input_dir_wsl = to_wsl_path(schp_input_dir_win)
        schp_output_dir_wsl = to_wsl_path(schp_output_dir_win)

        checkpoint_wsl = f"{schp_root_wsl}/checkpoints/exp-schp-201908261155-lip.pth"

        cmd = [
            "wsl",
            "bash",
            "-lc",
            (
                "source ~/miniconda3/etc/profile.d/conda.sh && "
                f"conda activate {SCHP_CONDA_ENV} && "
                "rm -rf ~/.cache/torch_extensions && "
                f"cd {schp_root_wsl} && "
                "CC=/usr/bin/gcc-12 "
                "CXX=/usr/bin/g++-12 "
                "CUDAHOSTCXX=/usr/bin/g++-12 "
                "CUDA_VISIBLE_DEVICES=0 "
                "python simple_extractor.py "
                "--dataset lip "
                f"--model-restore {checkpoint_wsl} "
                f"--input-dir {schp_input_dir_wsl} "
                f"--output-dir {schp_output_dir_wsl} "
                "--gpu 0"
            )
        ]

        print("[INFO] WSL SCHP command:")
        print(" ".join(cmd))

        result = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
        )

        if result.stdout:
            print("\n[SCHP STDOUT]")
            print(result.stdout)

        if result.stderr:
            print("\n[SCHP STDERR]")
            print(result.stderr)

        print(f"[INFO] SCHP returncode = {result.returncode}")

        for _ in range(60):
            pngs = list(schp_output_dir_win.glob("*.png"))
            if pngs:
                break
            time.sleep(1)
        else:
            raise RuntimeError(
                "SCHP 실행 실패: 결과 png가 생성되지 않았습니다.\n"
                f"returncode={result.returncode}"
            )

        out_files = sorted(schp_output_dir_win.glob("*.png"))
        if not out_files:
            raise FileNotFoundError(f"SCHP 결과가 없습니다: {schp_output_dir_win}")

        for src in out_files:
            dst = parse_dir / src.name
            shutil.copy2(src, dst)
            postprocess_cihp_parse(dst)

        print("[DONE] SCHP 완료 (후처리 포함)")
    finally:
        clear_dir(schp_input_dir_win)
        clear_dir(schp_output_dir_win)
        print("[CLEANUP] SCHP input/output 정리 완료")

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"[TIME] SCHP 총 소요 시간: {elapsed:.2f}초 ({elapsed/60:.2f}분)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_schp.py <job_dir>")

    job_dir = Path(sys.argv[1])

    paths = {
        "job_dir": job_dir,
        "image_dir": job_dir / "input" / "image",
        "parse_dir": job_dir / "preprocess" / "image-parse-v3",
    }

    run_schp(paths)
