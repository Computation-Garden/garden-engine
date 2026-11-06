from pathlib import Path

import frontmatter
import yaml


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ROOT / "sections"


def discover_articles():
	sections = []
	all_ids = set()

	for section_dir in sorted(SECTIONS.iterdir()):
		if not section_dir.is_dir():
			continue

		config_file = section_dir / "section.yml"

		if not config_file.exists():
			print(f"Skipping {section_dir.name}: missing section.yml")
			continue

		with config_file.open(encoding="utf-8") as f:
			section = yaml.safe_load(f)

		required = ("id", "title", "articles_directory")

		for key in required:
			if key not in section:
				raise ValueError(
					f"{config_file}: missing field '{key}'"
				)

		article_dir = section_dir / section["articles_directory"]

		if not article_dir.is_dir():
			raise ValueError(f"Missing article directory: {article_dir}")

		articles = []

		for article_file in sorted(article_dir.rglob("index.md")):
			post = frontmatter.load(article_file)
			metadata = dict(post.metadata)

			article_id = metadata.get("id")

			if not article_id:
				raise ValueError(f"Missing article ID: {article_file}")

			if article_id in all_ids:
				raise ValueError(f"Duplicate article ID: {article_id}")

			all_ids.add(article_id)

			articles.append({
				**metadata,
				"content": post.content,
				"section": section["id"],
				"source": article_file,
				"relative_source": article_file.relative_to(section_dir),
			})

		articles.sort(
			key=lambda a: (
				a.get("order", 999999),
				a["id"]
			)
		)

		sections.append({
			**section,
			"source": section_dir,
			"articles": articles,
		})

	return sections


if __name__ == "__main__":
	sections = discover_articles()

	total = sum(len(s["articles"]) for s in sections)

	print(f"Discovered {len(sections)} sections")
	print(f"Discovered {total} articles")

	for section in sections:
		print(f"\n{section['title']}")

		for article in section["articles"]:
			print(f"  - {article['id']}")
