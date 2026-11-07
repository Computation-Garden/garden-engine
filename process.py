import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WORK_DIR = ROOT / "build" / "work"
OUTPUT_DIR = ROOT / "computation-garden" / "sections"

build_script = WORK_DIR / "build.sh"

subprocess.run(
	["bash", str(build_script)],
	cwd=ROOT,
	check=True
)

if OUTPUT_DIR.exists():
	shutil.rmtree(OUTPUT_DIR)

shutil.copytree(WORK_DIR, OUTPUT_DIR)

destymlpath = OUTPUT_DIR.parent / "_data" / "sections.yml"
destymlpath.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(WORK_DIR.parent / "_data" / "sections.yml", destymlpath)

if (OUTPUT_DIR.parent / "_sass" / "sections_colors").exists():
	shutil.rmtree(OUTPUT_DIR.parent / "_sass" / "sections_colors")
shutil.copytree(WORK_DIR.parent / "_sass", OUTPUT_DIR.parent / "_sass" / "sections_colors")

print(f"Build complete! Copied {WORK_DIR} -> {OUTPUT_DIR}")
