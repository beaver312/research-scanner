"""
Example 4: Working with Paper Data Programmatically

Shows how to access and analyze paper metadata after scanning.
"""

from research_scanner.template_manager import TemplateManager
from research_scanner.scanner import ResearchScanner
from research_scanner.config import ScannerConfig
from collections import Counter
from datetime import datetime

print("=" * 70)
print("WORKING WITH PAPER DATA")
print("=" * 70)
print()

# Load a template and scan
manager = TemplateManager()
template = manager.load_template('ai_ml')
manager.save_template('user_config', template)

config = ScannerConfig.from_template('user_config')
scanner = ResearchScanner(config)

print("Running scan...")
papers = scanner.fetch_all_papers()
print(f"Found {len(papers)} papers\n")

if not papers:
    print("No papers found (all already indexed)")
    print("Try running after a few hours or with a different template")
    exit(0)

# Analysis 1: Papers by source
print("=" * 70)
print("ANALYSIS 1: Papers by Source")
print("=" * 70)
by_source = Counter(p.source for p in papers)
for source, count in by_source.most_common():
    percentage = (count / len(papers)) * 100
    print(f"  {source}: {count} papers ({percentage:.1f}%)")
print()

# Analysis 2: Papers by month
print("=" * 70)
print("ANALYSIS 2: Papers by Month")
print("=" * 70)
by_month = Counter(p.published_date.strftime('%Y-%m') for p in papers)
for month, count in sorted(by_month.items(), reverse=True)[:5]:
    print(f"  {month}: {count} papers")
print()

# Analysis 3: Most prolific authors
print("=" * 70)
print("ANALYSIS 3: Most Prolific Authors (in this batch)")
print("=" * 70)
all_authors = []
for paper in papers:
    all_authors.extend(paper.authors)
author_counts = Counter(all_authors)
for author, count in author_counts.most_common(10):
    print(f"  {author}: {count} paper(s)")
print()

# Analysis 4: Paper metadata example
print("=" * 70)
print("ANALYSIS 4: Detailed Paper Metadata Example")
print("=" * 70)
sample_paper = papers[0]
print(f"Title: {sample_paper.title}")
print(f"Authors: {', '.join(sample_paper.authors)}")
print(f"Source: {sample_paper.source}")
print(f"Published: {sample_paper.published_date.strftime('%Y-%m-%d')}")
print(f"URL: {sample_paper.url}")
if sample_paper.categories:
    print(f"Categories: {', '.join(sample_paper.categories)}")
print(f"\nAbstract (first 200 chars):")
print(f"{sample_paper.abstract[:200]}...")
print()

# Analysis 5: Average abstract length
print("=" * 70)
print("ANALYSIS 5: Abstract Statistics")
print("=" * 70)
abstract_lengths = [len(p.abstract) for p in papers]
avg_length = sum(abstract_lengths) / len(abstract_lengths)
min_length = min(abstract_lengths)
max_length = max(abstract_lengths)
print(f"  Average length: {avg_length:.0f} characters")
print(f"  Shortest: {min_length} characters")
print(f"  Longest: {max_length} characters")
print()

# Export to CSV example
print("=" * 70)
print("BONUS: Exporting to CSV")
print("=" * 70)
import csv

filename = f"papers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Authors', 'Source', 'Date', 'URL', 'Abstract'])
    for paper in papers:
        writer.writerow([
            paper.title,
            '; '.join(paper.authors),
            paper.source,
            paper.published_date.strftime('%Y-%m-%d'),
            paper.url,
            paper.abstract[:500]  # Truncate for CSV
        ])

print(f"Exported {len(papers)} papers to: {filename}")
print()
print("=" * 70)
print("You can now:")
print("  1. Open the CSV in Excel/Google Sheets")
print("  2. Run additional analysis in pandas")
print("  3. Create visualizations")
print("  4. Share with colleagues")
print("=" * 70)
