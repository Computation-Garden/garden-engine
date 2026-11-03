from pathlib import Path
import re
import subprocess
import sys
import yaml


ROOT = Path(__file__).resolve().parents[1]
SECTIONS_DIR = ROOT / "sections"


def slugify(value):
	value = value.lower().strip()
	value = re.sub(r"[^a-z0-9]+", "-", value)
	return value.strip("-")

def ask(question, default=None):
	if default is not None:
		answer = input(f"{question} [{default}]: ").strip()
		return answer or default

	while True:
		answer = input(f"{question}: ").strip()

		if answer:
			return answer

		print("This field is required.")


def ask_yes_no(question, default=True):
	suffix = "Y/n" if default else "y/N"

	answer = input(f"{question} [{suffix}]: ").strip().lower()

	if not answer:
		return default

	return answer in ("y", "yes")


def ask_list(question):
	answer = input(question).strip()

	if not answer:
		return []

	return [
		item.strip()
		for item in answer.split(",")
		if item.strip()
	]


def write_yaml(path, data):
	path.write_text(
		yaml.safe_dump(
			data,
			sort_keys=False,
			allow_unicode=True,
			default_flow_style=False
		),
		encoding="utf-8"
	)


def write_file(path, content):
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(content, encoding="utf-8")


def humanize(slug):
	return slug.replace("-", " ").title()


# --------------------------------------------------
# Collect config stuff
# --------------------------------------------------
def collect_information():
	print("[1] BASIC INFORMATION")
	print()

	title = ask("Section title")

	section_id = ask(
		"Section ID",
		slugify(title)
	)

	if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", section_id):
		raise ValueError(
			"Section ID must contain lowercase letters, "
			"numbers and hyphens only."
		)

	description = ask("Description")

	print()
	print("[2] STRUCTURE")
	print()

	articles_directory = ask(
		"Articles directory",
		"articles"
	)

	if (
		Path(articles_directory).is_absolute()
		or ".." in Path(articles_directory).parts
	):
		raise ValueError("Articles directory must be a relative path.")

	url_prefix = ask(
		"URL prefix",
		f"/{section_id}/"
	)

	if not url_prefix.startswith("/") or not url_prefix.endswith("/"):
		raise ValueError(
			"URL prefix must begin and end with '/'."
		)

	print()
	print("[4] GIT")
	print()

	initialize_git = ask_yes_no(
		"Initialize a Git repository?",
		True
	)

	return {
		"title": title,
		"id": section_id,
		"description": description,
		"articles_directory": articles_directory,
		"url_prefix": url_prefix,
		"initialize_git": initialize_git
	}


# --------------------------------------------------
# Template generation
# --------------------------------------------------
def create_section(info):
	section_path = SECTIONS_DIR / info["id"]

	if section_path.exists():
		raise FileExistsError(
			f"Section already exists: {section_path}"
		)

	section_path.mkdir(parents=True)

	# Section metadata

	section_config = {
		"id": info["id"],
		"title": info["title"],
		"description": info["description"],
		"articles_directory": info["articles_directory"],
		"url_prefix": info["url_prefix"],
		"enabled": True
	}

	write_yaml(
		section_path / "section.yml",
		section_config
	)

	# README

	readme = f"""# {info['title']}

{info['description']}

## Section information

- ID: `{info['id']}`
- URL prefix: `{info['url_prefix']}`
- Articles directory: `{info['articles_directory']}`

## Structure

```text
{info['id']}/
├── section.yml
└── {info['articles_directory']}/
```

## Adding articles

Create a directory for each article inside
`{info['articles_directory']}/`.

Each article should contain an `index.md` file
with valid YAML front matter.

## Building

This section is processed by the Computation Garden
content engine in the main website repository.
"""

	write_file(section_path / "README.md", readme)

	# Gitignore

	gitignore = """__pycache__/
*.pyc
.DS_Store

# LaTeX temporary files
*.aux
*.log
*.fls
*.fdb_latexmk
*.synctex.gz

# Local build output
_site/
build/
"""

	subprocess.run(
		["mkdir", info["articles_directory"]],
		cwd=section_path,
		check=True
	)
	
	subprocess.run(
		["mkdir", "sample"],
		cwd=section_path / info["articles_directory"],
		check=True
	)
	
	metadata = {
		"category": info["id"],
		"tags": [],
		"title": "Sample Article",
		"references": [],
		"prerequisites": [],
		"related": [],
		"status": "draft",
		"math": True
	}
	
	frontmatter = yaml.safe_dump(
		metadata,
		sort_keys=False,
		allow_unicode=True
	)
	
	samplemd = f"""---
{frontmatter.strip()}
---

# Sample Article

Lorem ipsum dolor...
"""

	write_file(section_path / info["articles_directory"] / "sample" / "index.md", samplemd)

	write_file(section_path / ".gitignore", gitignore)
	
	if info["initialize_git"]:

		subprocess.run(
			["git", "init"],
			cwd=section_path,
			check=True
		)

	return section_path


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():

	try:

		info = collect_information()

		print()
		print("=" * 52)
		print("CONFIRMATION")
		print("=" * 52)

		print(f"Section: {info['title']}")
		print(f"ID: {info['id']}")
		print(f"Articles directory: {info['articles_directory']}")
		print(f"URL prefix: {info['url_prefix']}")
		print(f"Git initialization: {'Yes' if info['initialize_git'] else 'No'}")

		print()

		if not ask_yes_no("Create section?", True):
			print("Cancelled.")
			return

		section_path = create_section(info)

		print()
		print("=" * 52)
		print("SECTION CREATED SUCCESSFULLY!")
		print("=" * 52)

		print()
		print(f"Location: {section_path}")
		print()
		print("Next steps:")
		print(f"1. cd {section_path}")
		print("2. Add your articles and content.")
		print("3. Create a remote Git repository.")
		print("4. Add the remote and push your section.")
		print("5. Add it to the main website as a submodule.")
		print()

	except (ValueError, FileExistsError, subprocess.CalledProcessError) as error:

		print()
		print(f"ERROR: {error}")
		sys.exit(1)


if __name__ == "__main__":
	main()