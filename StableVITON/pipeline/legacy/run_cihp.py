import subprocess
import shutil
import time
from pathlib import Path
import sys
from postprocess_cihp_parse import postprocess_cihp_parse

import time


def to_wsl_path(win_path: Path) -> str:
    s = str(win_path).replace("\\", "/")
    drive = s[0].lower()
    rest = s[2:]
    return f"/mnt/{drive}{rest}"


def run_cihp(paths):
    start_time = time.time()
    print("[TIME] CIHP_PGN 시작")

    image_dir = paths["image_dir"]
    parse_dir = paths["parse_dir"]

    cihp_root_win = Path(r"C:\Users\asd\Desktop\project\CIHP_PGN")
    cihp_input_dir_win = cihp_root_win / "datasets" / "CIHP" / "images"

    cihp_input_dir_win.mkdir(parents=True, exist_ok=True)

    # 입력 폴더 비우기
    for old_file in list(cihp_input_dir_win.iterdir()):
        if old_file.is_file():
            old_file.unlink()

    # 현재 job 이미지 복사
    copied = []
    for img_path in image_dir.iterdir():
        if img_path.is_file():
            dst = cihp_input_dir_win / img_path.name
            shutil.copy2(img_path, dst)
            copied.append(dst)

    if not copied:
        raise FileNotFoundError(f"CIHP 입력 이미지가 없습니다: {image_dir}")

    # 출력 폴더 비우기
    if parse_dir.exists():
        shutil.rmtree(parse_dir)
    parse_dir.mkdir(parents=True, exist_ok=True)

    cihp_root_wsl = to_wsl_path(cihp_root_win)
    cihp_input_dir_wsl = to_wsl_path(cihp_input_dir_win)
    parse_dir_wsl = to_wsl_path(parse_dir)

    cmd = [
        "wsl",
        "bash",
        "-lc",
        (
            "source ~/miniconda3/etc/profile.d/conda.sh && "
            "conda activate cihp_wsl && "
            f"cd {cihp_root_wsl} && "
            f"python inf_pgn.py -i {cihp_input_dir_wsl} -o {parse_dir_wsl}"
        )
    ]

    print("[INFO] WSL CIHP command:")
    print(" ".join(cmd))

    result = subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True
    )

    if result.stdout:
        print("\n[CIHP STDOUT]")
        print(result.stdout)

    if result.stderr:
        print("\n[CIHP STDERR]")
        print(result.stderr)

    print(f"[INFO] CIHP returncode = {result.returncode}")

    parsing_dir = parse_dir / "cihp_parsing_maps"
    edge_dir = parse_dir / "cihp_edge_maps"

    # 결과 생성 대기
    for _ in range(60):
        parsing_exists = parsing_dir.exists() and any(parsing_dir.iterdir())
        edge_exists = edge_dir.exists() and any(edge_dir.iterdir())
        if parsing_exists or edge_exists:
            break
        time.sleep(1)
    else:
        raise RuntimeError(
            "CIHP_PGN 실행 실패: 결과 파일이 생성되지 않았습니다.\n"
            f"returncode={result.returncode}"
        )

    # vis 파일 제외하고 실제 라벨맵 png만 선택
    parse_files = sorted([p for p in parsing_dir.glob("*.png") if not p.name.endswith("_vis.png")])

    if not parse_files:
        raise FileNotFoundError(f"CIHP parsing 결과가 없습니다: {parsing_dir}")

    for parse_file in parse_files:
        postprocess_cihp_parse(parse_file)

    print("[DONE] CIHP_PGN 완료 (후처리 포함)")

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"[TIME] CIHP_PGN 총 소요 시간: {elapsed:.2f}초 ({elapsed/60:.2f}분)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("사용법: python run_cihp.py <job_dir>")
    job_dir = Path(sys.argv[1])

    paths = {
        "job_dir": job_dir,
        "image_dir": job_dir / "input" / "image",
        "parse_dir": job_dir / "preprocess" / "image-parse-v3",
    }

    run_cihp(paths)