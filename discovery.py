from pathlib import Path
import frontmatter
import yaml


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ROOT / "sections"


def discover_articles():
	articles = []

	for section_dir in SECTIONS.iterdir():
		if not section_dir.is_dir():
			continue

		config_file = section_dir / "section.yml"

		if not config_file.exists():
			print(f"Skipping {section_dir.name}: missing section.yml")
			continue

		with config_file.open(encoding="utf-8") as f:
			section = yaml.safe_load(f)

		article_dir = section_dir / section["articles_directory"]

		for article_file in article_dir.rglob("index.md"):
			post = frontmatter.load(article_file)

			metadata = dict(post.metadata)

			articles.append({
				**metadata,
				"content": post.content,
				"section": section["id"],
				"source": str(article_file),
			})

	return articles


if __name__ == "__main__":
	articles = discover_articles()

	print(f"Discovered {len(articles)} articles")

	for article in articles:
		print(f"- {article['id']}: {article['title']}")