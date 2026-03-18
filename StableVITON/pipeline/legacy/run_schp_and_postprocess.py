import subprocess
from pathlib import Path
from postprocess_cihp_parse import postprocess_cihp_parse

input_dir = Path(r"C:\Users\asd\Desktop\custom_dataset\image")
output_dir = Path(r"C:\Users\asd\Desktop\custom_dataset\image-parse-v3")
schp_root = Path(r"C:\Users\asd\Desktop\project\Self-Correction-Human-Parsing")

output_dir.mkdir(parents=True, exist_ok=True)

def to_wsl_path(win_path: Path) -> str:
    s = str(win_path).replace("\\", "/")
    drive = s[0].lower()
    rest = s[2:]
    return f"/mnt/{drive}{rest}"

input_dir_wsl = to_wsl_path(input_dir)
output_dir_wsl = to_wsl_path(output_dir)
schp_root_wsl = to_wsl_path(schp_root)

cmd = [
    "wsl",
    "bash",
    "-lc",
    (
        "source ~/miniconda3/etc/profile.d/conda.sh && "
        "conda activate schp && "
        f"cd {schp_root_wsl} && "
        "python simple_extractor.py "
        "--dataset lip "
        f"--model-restore {schp_root_wsl}/checkpoints/exp-schp-201908261155-lip.pth "
        f"--input-dir {input_dir_wsl} "
        f"--output-dir {output_dir_wsl}"
    )
]

print("[INFO] SCHP command:")
print(" ".join(cmd))

result = subprocess.run(
    cmd,
    text=True,
    encoding="utf-8",
    errors="ignore",
    capture_output=True
)

if result.stdout:
    print("\n[SCHP STDOUT]")
    print(result.stdout)

if result.stderr:
    print("\n[SCHP STDERR]")
    print(result.stderr)

print(f"[INFO] returncode = {result.returncode}")

png_files = sorted(output_dir.glob("*.png"))
if not png_files:
    raise FileNotFoundError(f"SCHP 결과 png가 없습니다: {output_dir}")

for f in png_files:
    postprocess_cihp_parse(f)

print(f"[DONE] SCHP + 후처리 완료: {len(png_files)}개")