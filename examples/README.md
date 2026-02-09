# Research Scanner - Examples

This directory contains example scripts showing how to use Research Scanner.

## Quick Reference

| Example | Description | Difficulty |
|---------|-------------|------------|
| `1_quick_start.py` | Fastest way to get started | Beginner |
| `2_switching_domains.py` | Switch between research fields | Beginner |
| `3_custom_template.py` | Create your own domain template | Intermediate |
| `4_paper_analysis.py` | Analyze and export paper data | Intermediate |

---

## Example 1: Quick Start

**File:** `1_quick_start.py`  
**What it does:** Shows the fastest path from installation to scanning papers  
**Run time:** 30-60 seconds  

```bash
python examples/1_quick_start.py
```

**You'll learn:**
- How to load a pre-built template
- How to configure the scanner
- How to run your first scan
- How to view results

---

## Example 2: Switching Domains

**File:** `2_switching_domains.py`  
**What it does:** Demonstrates how easy it is to switch research fields  
**Run time:** <5 seconds  

```bash
python examples/2_switching_domains.py
```

**You'll learn:**
- How to list all available templates
- How different domains use different sources
- How topics change between fields
- The concept of domain adaptation

---

## Example 3: Custom Template

**File:** `3_custom_template.py`  
**What it does:** Creates a custom "Environmental Science" template from scratch  
**Run time:** <5 seconds  

```bash
python examples/3_custom_template.py
```

**You'll learn:**
- How to define a new research domain
- How to configure sources and topics
- How to set relevance thresholds
- How to save custom templates

**Result:** Creates `research_scanner/templates/environmental_science.yaml`

---

## Example 4: Paper Analysis

**File:** `4_paper_analysis.py`  
**What it does:** Analyzes paper metadata and exports to CSV  
**Run time:** 30-60 seconds  

```bash
python examples/4_paper_analysis.py
```

**You'll learn:**
- How to access paper metadata programmatically
- How to analyze sources and authors
- How to export data to CSV
- How to build custom analytics

**Result:** Creates `papers_export_YYYYMMDD_HHMMSS.csv`

---

## Running Examples

### Prerequisites

1. **Installation:**
```bash
pip install -r requirements.txt
```

2. **Ollama (Optional but recommended):**
```bash
# Visit https://ollama.ai/ for installation
ollama pull phi3:3.8b  # Or your preferred model
```

### From Project Root

```bash
# Quick start
python examples/1_quick_start.py

# Switch domains
python examples/2_switching_domains.py

# Custom template
python examples/3_custom_template.py

# Paper analysis
python examples/4_paper_analysis.py
```

---

## Next Steps

After running these examples:

1. **Try different templates:**
   - Medical, Physics, Biology, Astronomy, etc.
   - See `TEMPLATE_CATALOG.md` for all 11 domains

2. **Create your own template:**
   - Use Example 3 as a starting point
   - See `docs/TEMPLATES.md` for detailed guide

3. **Integrate with your workflow:**
   - Schedule daily scans with cron/Task Scheduler
   - Build custom analysis scripts
   - Use the API for web integration

4. **Contribute back:**
   - Share your custom templates
   - Report bugs or suggest features
   - See `CONTRIBUTING.md`

---

## Common Questions

**Q: Why do some scans find 0 papers?**  
A: All papers are already indexed. Try again in a few hours or switch domains.

**Q: Can I run multiple examples at once?**  
A: Yes, but they'll use the same ChromaDB instance. Each will update `user_config.yaml`.

**Q: How do I delete indexed papers?**  
A: Delete the `chroma_db/` directory. Be careful - this deletes all indexed data!

**Q: Can I modify the examples?**  
A: Absolutely! They're meant as learning tools. Experiment and customize!

---

## Example Output

### Quick Start (Example 1)
```
======================================================================
RESEARCH SCANNER - QUICK START EXAMPLE
======================================================================

Step 1: Loading AI & Machine Learning template...
Step 2: Saving as active configuration...
Step 3: Initializing scanner...

Scanner configured with:
  - Domain: AI & Machine Learning
  - Topics: 11
  - Sources: 3

Step 4: Running scan (this may take 30-60 seconds)...

======================================================================
SCAN COMPLETE - Found 44 new papers!
======================================================================

Sample papers:
1. FastVMT: Eliminating Redundancy in Video Motion Transfer
   Authors: Yue Ma, Zhikai Wang, Tianhao Ren
   ... and 9 more
   Source: huggingface
   Date: 2026-02-05
...
```

---

## Troubleshooting

**Import errors:**
```bash
# Make sure you're in the project root
cd /path/to/scholars-terminal
python examples/1_quick_start.py
```

**ChromaDB errors:**
```bash
# Reinstall ChromaDB
pip uninstall chromadb
pip install chromadb>=0.4.0
```

**Network errors:**
```bash
# Check your internet connection
# arXiv and PubMed require internet access
```

---

For more help, see:
- Main README: `../README.md`
- Template Guide: `../docs/TEMPLATES.md`  
- Contributing: `../CONTRIBUTING.md`
- Issues: https://github.com/yourusername/research-scanner/issues
