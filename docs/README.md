# Documentation

Complete documentation for Research Scanner.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Installation Guide](INSTALLATION.md) | Setup instructions for all platforms |
| [Template Guide](TEMPLATES.md) | Creating custom research domains |
| [API Reference](API.md) | Programming with Research Scanner |
| [Examples](../examples/README.md) | Code examples and tutorials |

---

## Getting Started

### New Users

1. **[Install](INSTALLATION.md)** - Get Research Scanner running
2. **[Quick Start](../examples/1_quick_start.py)** - Your first scan
3. **[Choose a template](../TEMPLATE_CATALOG.md)** - Find your domain

### Intermediate Users

1. **[Switch domains](../examples/2_switching_domains.py)** - Try different fields
2. **[Analyze data](../examples/4_paper_analysis.py)** - Work with results
3. **[Custom templates](TEMPLATES.md)** - Create your domain

### Advanced Users

1. **[API Reference](API.md)** - Build integrations
2. **[Contributing](../CONTRIBUTING.md)** - Add features
3. **[Architecture](ARCHITECTURE.md)** - Understand internals

---

## Documentation Structure

```
docs/
├── README.md           # This file - documentation index
├── INSTALLATION.md     # Platform-specific installation
├── TEMPLATES.md        # Creating custom domains
├── API.md             # Programming reference
└── ARCHITECTURE.md    # System design (coming soon)

../
├── README.md          # Project overview
├── CHANGELOG.md       # Version history
├── CONTRIBUTING.md    # Contribution guide
├── TEMPLATE_CATALOG.md # All 11 domains
└── examples/          # Code examples
    ├── 1_quick_start.py
    ├── 2_switching_domains.py
    ├── 3_custom_template.py
    └── 4_paper_analysis.py
```

---

## Key Concepts

### Templates

**What:** YAML files defining research domains  
**Why:** Universal tool that adapts to any field  
**How:** Configure sources, topics, keywords  
**Learn:** [TEMPLATES.md](TEMPLATES.md)

### Sources

**What:** Where papers come from  
**Options:** arXiv, PubMed, HuggingFace  
**How:** Enable per template based on domain  
**Learn:** [TEMPLATES.md#source-configuration](TEMPLATES.md#source-configuration)

### Topics

**What:** Research areas you care about  
**Why:** For relevance scoring  
**How:** Keywords + weights  
**Learn:** [TEMPLATES.md#topic-definition](TEMPLATES.md#topic-definition)

### ChromaDB

**What:** Vector database for semantic search  
**Why:** Find similar papers, not just keywords  
**How:** Automatic indexing after each scan  
**Learn:** [API.md#chromadb-integration](API.md)

---

## Common Tasks

### Task: Install Research Scanner

**Guide:** [INSTALLATION.md](INSTALLATION.md)  
**Time:** 5-10 minutes  
**Requirements:** Python 3.8+, 2GB disk  

### Task: Run First Scan

**Guide:** [Quick Start Example](../examples/1_quick_start.py)  
**Time:** 30-60 seconds  
**Output:** Papers in ChromaDB  

### Task: Switch Research Domains

**Guide:** [Switching Domains Example](../examples/2_switching_domains.py)  
**Time:** <5 seconds  
**Method:** Load different template  

### Task: Create Custom Template

**Guide:** [TEMPLATES.md](TEMPLATES.md)  
**Time:** 15-30 minutes  
**Method:** Copy existing, modify YAML  

### Task: Export Paper Data

**Guide:** [Paper Analysis Example](../examples/4_paper_analysis.py)  
**Time:** <1 minute  
**Format:** CSV, JSON, or programmatic access  

### Task: Integrate with Code

**Guide:** [API.md](API.md)  
**Time:** Varies  
**Use:** Build custom tools  

---

## Troubleshooting

### Installation Issues

See [INSTALLATION.md#troubleshooting](INSTALLATION.md#troubleshooting)

Common issues:
- Python version too old
- ChromaDB version conflicts
- Missing dependencies
- Network/firewall blocks

### Template Issues

See [TEMPLATES.md#troubleshooting](TEMPLATES.md#troubleshooting)

Common issues:
- Low relevance (<50%)
- No papers found
- Wrong papers returned
- Source configuration errors

### Runtime Issues

**No papers found:**
- All papers already indexed
- Try different domain
- Adjust lookback period

**ChromaDB errors:**
- Disk space full
- Corrupted database
- Version mismatch

**Network errors:**
- arXiv rate limiting
- PubMed timeout
- No internet connection

---

## Best Practices

### For Researchers

1. **Start with pre-built template** - Don't reinvent
2. **Run scans regularly** - Daily or weekly
3. **Monitor relevance** - >70% is good
4. **Refine iteratively** - Templates improve over time

### For Developers

1. **Use virtual environments** - Isolate dependencies
2. **Read API docs** - Understand interfaces
3. **Check examples** - See working code
4. **Contribute back** - Share improvements

### For Contributors

1. **Read CONTRIBUTING.md** - Process and standards
2. **Test thoroughly** - All platforms
3. **Document well** - Code + templates
4. **Engage community** - Discussions, issues

---

## Additional Resources

### Project Resources

- **GitHub Repo:** https://github.com/yourusername/research-scanner
- **Issue Tracker:** https://github.com/yourusername/research-scanner/issues
- **Discussions:** https://github.com/yourusername/research-scanner/discussions

### External Resources

- **arXiv API:** https://arxiv.org/help/api/
- **PubMed API:** https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **ChromaDB Docs:** https://docs.trychroma.com/
- **Ollama Models:** https://ollama.ai/library

### Research Tools

- **Scholar's Terminal** - Full research assistant (inspiration for this project)
- **Zotero** - Reference management
- **Mendeley** - Paper organization
- **Connected Papers** - Citation graphs

---

## Version Information

**Current Version:** 1.0.0  
**Release Date:** February 9, 2026  
**Python Support:** 3.8+  
**Status:** Stable - Production Ready

---

## Getting Help

### Quick Answers

1. **Check documentation** - Most answers here
2. **Read examples** - See working code
3. **Search issues** - Someone may have asked

### Need More Help?

1. **GitHub Issues** - Bug reports, feature requests
2. **Discussions** - Questions, ideas, templates
3. **Email** - Critical/security issues only

---

## Contributing to Documentation

Found an error? Want to improve docs?

1. **Minor fixes:** Submit PR directly
2. **Major changes:** Open issue first
3. **New sections:** Discuss in issue

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

**Happy researching! 📚🔬🚀**
