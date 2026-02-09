# Template Creation Guide

Learn how to create custom research domain templates for Research Scanner.

---

## Table of Contents

1. [Template Basics](#template-basics)
2. [Template Structure](#template-structure)
3. [Source Configuration](#source-configuration)
4. [Topic Definition](#topic-definition)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Testing Templates](#testing-templates)

---

## Template Basics

### What is a Template?

A template defines a **research domain** for the scanner:
- What sources to use (arXiv, PubMed, HuggingFace)
- What topics to track
- How to score relevance
- How far back to look for papers

### Why Use Templates?

**Universal Adaptation:**
- Medical researchers get PubMed papers
- AI researchers get arXiv + HuggingFace
- Physicists get arXiv only
- **Same tool, different domains**

### Template Files

Templates are YAML files in `research_scanner/templates/`:

```
research_scanner/
└── templates/
    ├── ai_ml.yaml
    ├── medical_cardiac.yaml
    ├── physics_quantum.yaml
    └── your_template.yaml
```

---

## Template Structure

### Minimal Template

```yaml
domain: "Your Research Field"
description: "Brief description of what this template tracks"

sources:
  arxiv:
    enabled: true
    categories: ["your.category"]
  
  pubmed:
    enabled: false
  
  huggingface:
    enabled: false

topics:
  - name: "Your Main Topic"
    keywords: ["keyword1", "keyword2", "keyword3"]
    weight: 1.5

relevance_threshold: 0.3
days_lookback: 7
max_papers_per_scan: 50
```

### Complete Template Structure

```yaml
# Basic Info
domain: "String - Name of research field"
description: "String - What this template tracks"

# Source Configuration
sources:
  arxiv:
    enabled: boolean
    categories: ["list", "of", "arxiv.categories"]
  
  pubmed:
    enabled: boolean
    queries: ["list", "of", "search queries"]
    mesh_terms: ["optional", "mesh", "terms"]
  
  huggingface:
    enabled: boolean

# Research Topics
topics:
  - name: "Topic Name"
    keywords: ["keyword1", "keyword2"]
    weight: float (1.0-2.0)
    arxiv_categories: ["optional", "specific.categories"]

# Scanner Settings
relevance_threshold: float (0.0-1.0, typically 0.3-0.4)
days_lookback: int (typically 7-14)
max_papers_per_scan: int (typically 50-100)
```

---

## Source Configuration

### arXiv

**Best for:** Physical sciences, computer science, mathematics

```yaml
sources:
  arxiv:
    enabled: true
    categories:
      - "cs.AI"          # Artificial Intelligence
      - "cs.LG"          # Machine Learning
      - "physics.comp-ph" # Computational Physics
```

**Finding Categories:**
- Browse: https://arxiv.org/
- List: https://arxiv.org/category_taxonomy
- Popular categories:
  - CS: `cs.AI`, `cs.LG`, `cs.CV`, `cs.CL`, `cs.CR`
  - Physics: `physics.comp-ph`, `quant-ph`, `astro-ph`
  - Bio: `q-bio.GN`, `q-bio.MN`, `q-bio.NC`

### PubMed

**Best for:** Medical, biological, health sciences

```yaml
sources:
  pubmed:
    enabled: true
    queries:
      - "your research topic"
      - "specific medical condition"
      - "treatment OR therapy"
    mesh_terms:
      - "Medical Subject Heading"
      - "Another MeSH Term"
```

**Query Tips:**
- Be specific: "CRISPR gene editing" not just "genetics"
- Use operators: `AND`, `OR`, `NOT`
- Use quotes: `"exact phrase matching"`
- Combine: `"cardiac surgery" AND minimally invasive`

**Finding MeSH Terms:**
- Browse: https://www.ncbi.nlm.nih.gov/mesh
- Search your topic, find official MeSH terms
- More specific = better relevance

### HuggingFace

**Best for:** AI/ML research, especially recent work

```yaml
sources:
  huggingface:
    enabled: true
```

**Note:** HuggingFace doesn't use categories/queries. It fetches recent AI/ML papers automatically.

---

## Topic Definition

### Topic Structure

```yaml
topics:
  - name: "Human-Readable Topic Name"
    keywords: ["kw1", "kw2", "kw3", "kw4", "kw5"]
    weight: 1.5
    arxiv_categories: ["optional.category"]
```

### Topic Weights

Higher weight = more important topic:
- **1.5-2.0:** Core topics (highest priority)
- **1.2-1.4:** Important topics
- **1.0-1.1:** Related/supporting topics

**Example:**
```yaml
topics:
  - name: "Core Research Area"
    keywords: ["main", "focus"]
    weight: 1.8  # Highest priority

  - name: "Important Sub-area"
    keywords: ["related", "important"]
    weight: 1.3  # Medium priority

  - name: "Peripheral Topic"
    keywords: ["tangential", "background"]
    weight: 1.0  # Lower priority
```

### Keyword Selection

**Good Keywords:**
- ✅ Specific technical terms
- ✅ Common abbreviations
- ✅ Method names
- ✅ Domain jargon

**Bad Keywords:**
- ❌ Too generic ("data", "analysis")
- ❌ Too common ("research", "study")
- ❌ Single letters ("A", "B")

**Example - Good:**
```yaml
keywords: ["CRISPR", "gene editing", "cas9", "genome modification", "knockout"]
```

**Example - Bad:**
```yaml
keywords: ["genetics", "DNA", "research", "study", "new"]
```

---

## Advanced Features

### Topic-Specific arXiv Categories

Limit topic keywords to specific arXiv categories:

```yaml
topics:
  - name: "Quantum Computing"
    keywords: ["quantum computer", "qubit", "quantum gate"]
    weight: 1.5
    arxiv_categories: ["quant-ph", "cond-mat.mes-hall"]
  
  - name: "Classical Algorithms"
    keywords: ["algorithm", "optimization", "complexity"]
    weight: 1.2
    arxiv_categories: ["cs.DS", "cs.CC"]
```

### Multi-Source Templates

Combine sources for comprehensive coverage:

```yaml
sources:
  arxiv:
    enabled: true
    categories: ["q-bio.GN", "q-bio.MN"]  # Genomics
  
  pubmed:
    enabled: true
    queries:
      - "CRISPR gene editing"
      - "genomics sequencing"
  
  huggingface:
    enabled: false  # Not relevant for biology

# Now you get papers from both arXiv AND PubMed!
```

### Relevance Tuning

Adjust threshold based on specificity:

```yaml
# Specific domain (quantum physics)
relevance_threshold: 0.25  # Lower = more permissive

# Broad domain (general biology)  
relevance_threshold: 0.40  # Higher = more strict

# Multi-source (AI + medicine)
relevance_threshold: 0.35  # Medium
```

### Lookback Period

Adjust based on publication rate:

```yaml
# Fast-moving field (AI/ML)
days_lookback: 3  # Check every 3 days

# Medium pace (medical)
days_lookback: 7  # Weekly

# Slow-moving (archaeology)
days_lookback: 14  # Bi-weekly
```

---

## Best Practices

### 1. Start with Existing Template

```bash
# Copy similar template
cp research_scanner/templates/ai_ml.yaml \
   research_scanner/templates/my_field.yaml

# Edit for your domain
nano research_scanner/templates/my_field.yaml
```

### 2. Use Domain-Specific Sources

**Medical/Biology:**
```yaml
sources:
  pubmed:
    enabled: true  # Primary source
  arxiv:
    enabled: true  # q-bio categories
  huggingface:
    enabled: false  # Not relevant
```

**Computer Science:**
```yaml
sources:
  arxiv:
    enabled: true  # cs.* categories
  huggingface:
    enabled: true  # Recent AI papers
  pubmed:
    enabled: false  # Not relevant
```

### 3. Define 5-10 Topics

**Too few (<5):** Miss important sub-areas  
**Too many (>10):** Diluted relevance scoring  
**Sweet spot:** 5-8 well-defined topics

### 4. Weight Important Topics Higher

```yaml
# Core methodology
- name: "CRISPR Technology"
  weight: 1.8  # Highest

# Important application
- name: "Gene Therapy"
  weight: 1.4  # Medium

# Background context
- name: "Ethics & Regulation"
  weight: 1.0  # Lower
```

### 5. Test and Iterate

```bash
# Test your template
python test_your_template.py

# Check relevance
# Adjust keywords/weights
# Retest

# Aim for >70% relevance
```

---

## Examples

### Example 1: Environmental Science

```yaml
domain: "Environmental Science & Ecology"
description: "Climate change, conservation, pollution, ecosystem health"

sources:
  arxiv:
    enabled: true
    categories:
      - "physics.ao-ph"  # Atmospheric/Oceanic
      - "q-bio.PE"       # Populations & Evolution
  
  pubmed:
    enabled: true
    queries:
      - "climate change ecology"
      - "environmental pollution health"
      - "conservation biology"
    mesh_terms:
      - "Climate Change"
      - "Ecosystem"
      - "Environmental Pollution"
  
  huggingface:
    enabled: false

topics:
  - name: "Climate Change & Modeling"
    keywords: ["climate model", "global warming", "carbon emissions"]
    weight: 1.5
    arxiv_categories: ["physics.ao-ph"]

  - name: "Biodiversity & Conservation"
    keywords: ["biodiversity", "endangered species", "habitat loss"]
    weight: 1.4

  - name: "Environmental Pollution"
    keywords: ["pollution", "contamination", "microplastics", "air quality"]
    weight: 1.3

relevance_threshold: 0.30
days_lookback: 7
max_papers_per_scan: 50
```

### Example 2: Cybersecurity

```yaml
domain: "Cybersecurity & Information Security"
description: "Network security, cryptography, threat detection, privacy"

sources:
  arxiv:
    enabled: true
    categories:
      - "cs.CR"  # Cryptography and Security
      - "cs.NI"  # Networking
  
  pubmed:
    enabled: false
  
  huggingface:
    enabled: true  # AI security papers

topics:
  - name: "Cryptography & Encryption"
    keywords: ["encryption", "cryptography", "public key", "zero knowledge"]
    weight: 1.5

  - name: "Network Security"
    keywords: ["firewall", "intrusion detection", "DDoS", "packet analysis"]
    weight: 1.4

  - name: "AI Security & Adversarial"
    keywords: ["adversarial", "model poisoning", "backdoor", "AI security"]
    weight: 1.4

  - name: "Privacy & Data Protection"
    keywords: ["privacy", "GDPR", "differential privacy", "data protection"]
    weight: 1.2

relevance_threshold: 0.35
days_lookback: 5
max_papers_per_scan: 50
```

---

## Testing Templates

### Test Script Template

```python
from research_scanner.template_manager import TemplateManager
from research_scanner.scanner import ResearchScanner
from research_scanner.config import ScannerConfig

# Load your template
manager = TemplateManager()
template = manager.load_template('your_template')
manager.save_template('user_config', template)

# Run scan
config = ScannerConfig.from_template('user_config')
scanner = ResearchScanner(config)
papers = scanner.fetch_all_papers()

# Analyze results
print(f"Found {len(papers)} papers")

# Check relevance
your_keywords = ["keyword1", "keyword2", "keyword3"]
relevant = sum(1 for p in papers 
               if any(kw.lower() in (p.title + p.abstract).lower() 
                     for kw in your_keywords))
relevance = (relevant / len(papers)) * 100 if papers else 0

print(f"Relevance: {relevance:.1f}%")
print(f"Target: >70%")

# Show samples
for i, paper in enumerate(papers[:3], 1):
    print(f"\n{i}. {paper.title}")
    print(f"   Source: {paper.source}")
```

### Interpreting Results

**Excellent (>80%):** Template is well-tuned  
**Good (60-80%):** Template works, minor tweaks needed  
**Needs Work (<60%):** Adjust keywords/categories/sources

### Iteration Process

1. **Run test** → Get relevance score
2. **Analyze papers** → What's not relevant?
3. **Adjust template:**
   - Add specific keywords
   - Remove generic keywords
   - Change categories
   - Adjust weights
4. **Retest** → Should improve
5. **Repeat** until >70% relevance

---

## Sharing Templates

### Contributing Your Template

1. **Test thoroughly** (>70% relevance)
2. **Document well** (clear description, good keywords)
3. **Submit PR** to GitHub
4. **Include test results** in PR description

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## Troubleshooting

**Low relevance (<50%):**
- Keywords too generic
- Wrong arXiv categories
- Wrong source combination

**No papers found:**
- Categories don't exist
- Queries too specific
- All papers already indexed

**Too many papers:**
- Increase `relevance_threshold`
- Use more specific keywords
- Narrow arXiv categories

---

**Ready to create your template? Start with Example 1 or 2 above! 🚀**
