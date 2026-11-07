import re
import shutil
from pathlib import Path
import json

from garden_engine.discovery import *

ROOT = Path(__file__).resolve().parents[1]

WORK_DIR = ROOT / "build" / "work"


def replace_custom_syntax(content, workspace):
	# This replaces:
	# 	{% diagram "xyz" %}
	# 	{% image "xyz" %}
	# 	{% code "xyz" %}
	# 	{% pele "xyz" %}
	patterns = {
		"diagram": {
			"directory": "diagrams",
			"render": lambda name, _: f'<img src="./diagrams/{name}">',
		},
		"image": {
			"directory": "images",
			"render": lambda name, _: f'<img src="./images/{name}">',
		},
		"code": {
			"directory": "code",
			"render": lambda name, source: f"```\n{source}\n```",
		},
		"pele": {
			"directory": "pele",
			"render": lambda name, source: (
				f'<pre class="mermaid">\n{source}\n</pre>'
			),
		},
	}

	pattern = re.compile(
		r'{% raw %}{%\s*(diagram|image|code|pele)\s+"([^"]+)"\s*%}{% endraw %}'
	)

	def replace(match):
		kind, name = match.groups()
		config = patterns[kind]

		if kind in ("diagram", "image"):
			return config["render"](name, None)

		source_file = workspace / config["directory"] / name

		if not source_file.is_file():
			raise FileNotFoundError(
				f"Missing {kind} file: {source_file}"
			)

		source = source_file.read_text(encoding="utf-8")

		return config["render"](name, source)

	return pattern.sub(replace, content)
	
def copy_section_banner(section, workspace):
	banner = section["banner"]

	if not banner:
		return

	source = WORK_DIR / section["source"] / banner

	if not source.is_file():
		raise FileNotFoundError(
			f"Missing banner file: {source}"
		)

	shutil.copy2(
		source,
		workspace / banner
	)

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

	# process md files
	for markdown_file in workspace.glob("*.md"):
		content = markdown_file.read_text(encoding="utf-8")

		content = replace_custom_syntax(content, workspace)

		content = f"""---
layout: cg_article
section_title: {section["title"]}
section_id: {section["id"]}
"""+content[4:]

		markdown_file.write_text(
			content,
			encoding="utf-8"
		)

	return workspace


def generate_sections_data(sections):
	data = [
		{
			"title": section["title"],
			"groups": section["groups"],
			"description": section["description"],
			"longdescription": section["longdescription"],
			"id": section["id"],
		}
		for section in sections
	]

	data_dir = WORK_DIR.parent / "_data"
	data_dir.mkdir(parents=True, exist_ok=True)

	output = data_dir / "sections.yml"

	output.write_text(
		json.dumps(data, ensure_ascii=False, indent=2) + "\n",
		encoding="utf-8"
	)


def generate_build_script(article, workspace):
	commands = [
		"#!/usr/bin/env bash",
		"set -euo pipefail",
		'ARTICLE_DIR="$(cd "$(dirname "$0")" && pwd)"',
		'OUTPUT_DIR="$ARTICLE_DIR/output"',
		'mkdir -p "$OUTPUT_DIR/diagrams"',
	]
	flag = 0

	for tex_file in sorted((workspace / "diagrams").glob("*.tex")):
		flag = 1
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
		
		commands.extend([
			"",
			f"# Move outputs out",
			(
				f'rm -rf "$ARTICLE_DIR/diagrams/"\n'
				f'mv "$OUTPUT_DIR/diagrams/" "$ARTICLE_DIR"\n'
				f'rm -rf "$OUTPUT_DIR"\n'
			),
		])

	script = workspace / "build.sh"

	script.write_text(
		"\n".join(commands) + "\n",
		encoding="utf-8"
	)

	script.chmod(0o755)

	return script


if __name__ == "__main__":
	sections = discover_articles()
	sections_file = generate_sections_data(sections)
	print(f"Generated sections data.")
	
	total = sum(len(s["articles"]) for s in sections)

	print(f"Discovered {len(sections)} sections")
	print(f"Discovered {total} articles")

	build_scripts = []


	
	style_dir = WORK_DIR.parent / "_sass"
	style_dir.mkdir(parents=True, exist_ok=True)
	sections_sass = []

	for section in sections:
		print(f"\n{section['title']}")

		workspace = WORK_DIR / section["id"]

		workspace.mkdir(parents=True, exist_ok=True)
		copy_section_banner(section, workspace)
		indexcontent = f"""---
title: {section["title"]}
layout: cg_section
id: {section["id"]}
description: {section["description"]}
longdescription: {section["longdescription"]}
banner: {section["banner"]}
---

# Articles
"""
		sass = style_dir / f"{section['id']}.sass"
		sections_sass.append(f"@forward '{section['id']}.sass'")
		sasscontent = f"""
@use 'colourdefs'
.{section["id"]}
	--theme-color: #{{colourdefs.${section["themecolor"]}}}
"""
		sass.write_text(sasscontent)
		
		print("Preprocessing articles...")

		for article in section["articles"]:
			print(f"  - {article['id']}")

			w = prepare_article(article, section)

			script = generate_build_script(article, w)
			build_scripts.append(script)

			s = (
				f'\n- [{article["title"]}]'
				f'(/sections/{article["section"]}/{article["id"]}/)'
			)

			indexcontent += s

		print("Generating index...")

		index = workspace / "index.md"

		index.write_text(
			indexcontent,
			encoding="utf-8"
		)

		print("Done.")

	sassidx = style_dir / f"_index.sass"
	sassidx.write_text("\n".join(sections_sass))

	print(f"\nGenerated {len(build_scripts)} build scripts and sass files.")
	
	


	main_build_script = WORK_DIR / "build.sh"
	with main_build_script.open("a", encoding="utf-8") as file:
		for script in build_scripts:
			file.write(str(script)+"\n")
	
	
	print("Done.")