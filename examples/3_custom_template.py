"""
Example 3: Creating a Custom Template

Shows how to create your own research domain template.
"""

from research_scanner.template_manager import TemplateManager, DomainTemplate, SourceConfig, TopicConfig

print("=" * 70)
print("CREATING A CUSTOM RESEARCH DOMAIN TEMPLATE")
print("=" * 70)
print()

print("Let's create a template for: Environmental Science")
print()

# Define custom template
environmental_template = DomainTemplate(
    domain="Environmental Science",
    description="Track climate change, ecology, conservation, and environmental policy research",
    
    # Configure sources
    sources={
        'arxiv': SourceConfig(
            enabled=True,
            categories=['physics.ao-ph', 'q-bio.PE']  # Atmospheric/Oceanic physics, Populations & Evolution
        ),
        'pubmed': SourceConfig(
            enabled=True,
            queries=[
                "climate change health",
                "environmental pollution",
                "ecosystem health",
                "conservation biology"
            ]
        ),
        'huggingface': SourceConfig(
            enabled=False
        )
    },
    
    # Define research topics
    topics=[
        TopicConfig(
            name="Climate Change & Modeling",
            keywords=["climate change", "climate model", "global warming", 
                     "carbon emissions", "temperature rise"],
            weight=1.5,
            arxiv_categories=['physics.ao-ph']
        ),
        TopicConfig(
            name="Biodiversity & Conservation",
            keywords=["biodiversity", "conservation", "endangered species",
                     "habitat loss", "ecosystem"],
            weight=1.4
        ),
        TopicConfig(
            name="Environmental Pollution",
            keywords=["pollution", "air quality", "water contamination",
                     "microplastics", "toxicology"],
            weight=1.3
        ),
        TopicConfig(
            name="Renewable Energy",
            keywords=["solar energy", "wind power", "renewable",
                     "sustainable energy", "green technology"],
            weight=1.2
        ),
        TopicConfig(
            name="Ocean & Marine Sciences",
            keywords=["ocean acidification", "coral reef", "marine ecology",
                     "overfishing", "sea level rise"],
            weight=1.2
        )
    ],
    
    # Scanner settings
    relevance_threshold=0.3,
    days_lookback=7,
    max_papers_per_scan=50
)

# Save the template
manager = TemplateManager()
manager.save_template('environmental_science', environmental_template)

print("Template created successfully!")
print()
print("=" * 70)
print("TEMPLATE DETAILS")
print("=" * 70)
print()
print(f"Domain: {environmental_template.domain}")
print(f"Description: {environmental_template.description}")
print()

print("Sources:")
for source, config in environmental_template.sources.items():
    if config.enabled:
        print(f"  [{source}]")
        if config.categories:
            print(f"    Categories: {', '.join(config.categories)}")
        if config.queries:
            print(f"    Queries: {len(config.queries)}")
print()

print("Topics:")
for i, topic in enumerate(environmental_template.topics, 1):
    print(f"  {i}. {topic.name} (weight: {topic.weight})")
    print(f"     Keywords: {', '.join(topic.keywords[:3])}...")
print()

print("Settings:")
print(f"  Relevance threshold: {environmental_template.relevance_threshold}")
print(f"  Days lookback: {environmental_template.days_lookback}")
print(f"  Max papers: {environmental_template.max_papers_per_scan}")
print()

print("=" * 70)
print("Template saved to: research_scanner/templates/environmental_science.yaml")
print()
print("To use it:")
print("  1. Load: manager.load_template('environmental_science')")
print("  2. Set as active: manager.save_template('user_config', template)")
print("  3. Run scan: python run_scan.py")
print("=" * 70)
