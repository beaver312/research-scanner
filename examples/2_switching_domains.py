"""
Example 2: Switching Between Research Domains

Shows how easy it is to switch from one research field to another.
"""

from research_scanner.template_manager import TemplateManager
from research_scanner.config import ScannerConfig

print("=" * 70)
print("SWITCHING RESEARCH DOMAINS")
print("=" * 70)
print()

manager = TemplateManager()

# List all available templates
print("Available templates:")
templates = ['ai_ml', 'medical_cardiac', 'aerospace', 'biology_genetics',
             'chemistry_materials', 'art_conservation', 'physics_quantum',
             'psychology', 'archaeology', 'astronomy', 'geology']

for i, template_name in enumerate(templates, 1):
    template = manager.load_template(template_name)
    print(f"{i:2}. {template.domain}")
    print(f"    Topics: {len(template.topics)}, "
          f"Sources: {', '.join(s for s, cfg in template.sources.items() if cfg.enabled)}")

print()
print("-" * 70)
print("EXAMPLE: Switching from AI to Medical Research")
print("-" * 70)
print()

# Load AI template
print("1. Currently using: AI & Machine Learning")
ai_template = manager.load_template('ai_ml')
ai_config = ScannerConfig.from_template_object(ai_template)
print(f"   Sources: arXiv={'Yes' if ai_config.arxiv_enabled else 'No'}, "
      f"PubMed={'Yes' if ai_config.pubmed_enabled else 'No'}, "
      f"HF={'Yes' if ai_config.huggingface_enabled else 'No'}")
print()

# Switch to Medical
print("2. Switching to: Medical - Cardiac Surgery")
medical_template = manager.load_template('medical_cardiac')
manager.save_template('user_config', medical_template)
medical_config = ScannerConfig.from_template('user_config')
print(f"   Sources: arXiv={'Yes' if medical_config.arxiv_enabled else 'No'}, "
      f"PubMed={'Yes' if medical_config.pubmed_enabled else 'No'}, "
      f"HF={'Yes' if medical_config.huggingface_enabled else 'No'}")
print()

print("Notice how sources changed!")
print("  - AI template uses: arXiv + HuggingFace + PubMed")
print("  - Medical template uses: PubMed ONLY")
print()
print("This is domain adaptation in action!")
print()

# Show topic differences
print("-" * 70)
print("Topic Differences:")
print("-" * 70)
print()
print("AI Topics:")
for topic in ai_template.topics[:3]:
    print(f"  - {topic.name}")
print(f"  ... and {len(ai_template.topics) - 3} more")
print()

print("Medical Topics:")
for topic in medical_template.topics[:3]:
    print(f"  - {topic.name}")
print(f"  ... and {len(medical_template.topics) - 3} more")
print()

print("=" * 70)
print("TIP: The system automatically adapts to your research domain!")
print("=" * 70)
