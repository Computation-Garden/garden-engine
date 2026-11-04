from pathlib import Path
import frontmatter
import yaml


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ROOT / "sections"


def discover_articles():
	articles = []

	for section_dir in sorted(SECTIONS.iterdir()):
		if not section_dir.is_dir():
			continue

		config_file = section_dir / "section.yml"

		if not config_file.exists():
			print(f"Skipping {section_dir.name}: missing section.yml")
			continue

		with config_file.open(encoding="utf-8") as f:
			section = yaml.safe_load(f) or {}

		section_id = section.get("id")

		if not section_id:
			raise ValueError(
				f"Missing section ID in {config_file}"
			)

		article_root = section_dir / section["articles_directory"]

		if not article_root.exists():
			raise FileNotFoundError(article_root)

		for article_file in sorted(
			article_root.rglob("index.md")
		):
			post = frontmatter.load(article_file)

			metadata = dict(post.metadata)

			articles.append({
				**metadata,

				# actual content
				"content": post.content,

				# section info
				"section": section_id,
				"section_title": section.get("title", section_id),
				"position_in_section": section["order"].index(metadata["id"]),

				# fs information
				"_source": article_file,
				"_article_dir": article_file.parent,
				"_article_root": article_root,
			})

	return articles

if __name__ == "__main__":
	articles = discover_articles()

	print(f"Discovered {len(articles)} articles")

	for article in articles:
		print(f"{article['section']}:{article['position_in_section']}>>{article['id']}: {article['title']}")