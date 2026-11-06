import shutil
from pathlib import Path
from garden_engine.discovery import *

ROOT = Path(__file__).resolve().parents[1]

WORK_DIR = ROOT / "build" / "work"


def prepare_article(article, section):
	workspace = (
		WORK_DIR
		/ section["id"]
		/ article["id"]
	)

	if workspace.exists():
		shutil.rmtree(workspace)

	workspace.mkdir(parents=True)

	source_dir = article["source"].parent

	for item in source_dir.iterdir():
		destination = workspace / item.name

		if item.is_dir():
			shutil.copytree(item, destination)
		else:
			shutil.copy2(item, destination)

	return workspace
	
def generate_build_script(article, workspace):
	commands = [
		"#!/usr/bin/env bash",
		"set -euo pipefail",
		'ARTICLE_DIR="$(cd "$(dirname "$0")" && pwd)"',
		'OUTPUT_DIR="$ARTICLE_DIR/output"',
		'mkdir -p "$OUTPUT_DIR/diagrams"',
	]

	for tex_file in sorted((workspace / "diagrams").glob("*.tex")):
		name = tex_file.stem

		commands.extend([
			"",
			f"# Compile {name}",
			(
				'latexmk -pdf -interaction=nonstopmode '
				'-halt-on-error '
				f'-outdir="$OUTPUT_DIR" '
				f'"$ARTICLE_DIR/diagrams/{tex_file.name}"'
			),
			(
				f'pdftocairo -svg "$OUTPUT_DIR/{name}.pdf" '
				f'"$OUTPUT_DIR/diagrams/{name}.svg"'
			),
		])

	script = workspace / "build.sh"

	script.write_text(
		"\n".join(commands) + "\n",
		encoding="utf-8"
	)

	script.chmod(0o755)
	
if __name__ == "__main__":
	sections = discover_articles()

	total = sum(len(s["articles"]) for s in sections)

	print(f"Discovered {len(sections)} sections")
	print(f"Discovered {total} articles")

	for section in sections:
		print(f"\n{section['title']}")

		workspace = (
			WORK_DIR
			/ section["id"]
		)

		
		indexcontent = f"""
# {section["title"]}
{section["description"]}

## Articles
"""
		print("Preprocessing articles...")
		for article in section["articles"]:
			print(f"  - {article['id']}")
			w = prepare_article(article, section)
			generate_build_script(article, w)
			s = f'\n- [{article["title"]}](/{article["section"]}/{article["id"]}/)'
			indexcontent=indexcontent+s
			

		print("Generating index...")
		index = workspace / "index.md"
		
		index.write_text(
			indexcontent,
			encoding="utf-8"
		)
		
		print("Done.")