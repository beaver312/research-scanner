"""
Example 1: Quick Setup and First Scan

This example shows the fastest way to get started with Research Scanner.
"""

from research_scanner.template_manager import TemplateManager
from research_scanner.scanner import ResearchScanner
from research_scanner.config import ScannerConfig

print("=" * 70)
print("RESEARCH SCANNER - QUICK START EXAMPLE")
print("=" * 70)
print()

# Step 1: Choose a template
print("Step 1: Loading AI & Machine Learning template...")
manager = TemplateManager()
template = manager.load_template('ai_ml')

# Step 2: Save as your active configuration
print("Step 2: Saving as active configuration...")
manager.save_template('user_config', template)

# Step 3: Create scanner with your config
print("Step 3: Initializing scanner...")
config = ScannerConfig.from_template('user_config')
scanner = ResearchScanner(config)

print(f"\nScanner configured with:")
print(f"  - Domain: {template.domain}")
print(f"  - Topics: {len(template.topics)}")
print(f"  - Sources: {len(scanner.sources)}")
print()

# Step 4: Run your first scan
print("Step 4: Running scan (this may take 30-60 seconds)...")
papers = scanner.fetch_all_papers()

print()
print("=" * 70)
print(f"SCAN COMPLETE - Found {len(papers)} new papers!")
print("=" * 70)
print()

# Step 5: Show results
if papers:
    print("Sample papers:")
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        if len(paper.authors) > 3:
            print(f"   ... and {len(paper.authors) - 3} more")
        print(f"   Source: {paper.source}")
        print(f"   Date: {paper.published_date.strftime('%Y-%m-%d')}")
    
    if len(papers) > 5:
        print(f"\n... and {len(papers) - 5} more papers")
    
    print()
    print("Papers are now indexed in ChromaDB!")
    print("You can search them using Scholar's Terminal or the API.")
else:
    print("No new papers found (all already indexed)")

print()
print("=" * 70)
print("Next steps:")
print("  1. Try a different template: python examples/2_switching_domains.py")
print("  2. Create custom template: python examples/3_custom_template.py")
print("  3. Start the API: python Scholars_api.py")
print("=" * 70)
