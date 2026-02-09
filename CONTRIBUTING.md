# Contributing to Research Scanner

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## 🌟 Ways to Contribute

### 1. Create Domain Templates
The easiest and most valuable contribution! If you're an expert in a research field, create a template for it.

**Steps:**
1. Copy an existing template from `research_scanner/templates/`
2. Modify for your domain
3. Test with `python test_template_integration.py`
4. Submit PR with your template

**We especially need:**
- Engineering domains (electrical, mechanical, civil)
- Medical specialties (oncology, neurology, pediatrics)
- Social sciences (economics, sociology, political science)
- Humanities (history, philosophy, literature)

### 2. Add New Sources
Help expand paper sources beyond arXiv, PubMed, and HuggingFace.

**Wanted sources:**
- IEEE Xplore (engineering)
- medRxiv (medical preprints)
- bioRxiv (biology preprints)
- SSRN (social sciences)
- JSTOR (humanities)
- Semantic Scholar (cross-domain)

**Steps:**
1. Create new source class in `research_scanner/sources/`
2. Inherit from `BaseSource`
3. Implement `fetch_recent()` and `search()` methods
4. Add tests
5. Update templates that would benefit

### 3. Improve Documentation
- Fix typos or unclear sections
- Add examples
- Translate README to other languages
- Create video tutorials

### 4. Report Bugs
Open an issue with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)
- Relevant logs

### 5. Suggest Features
Open an issue with:
- Use case description
- Why it's valuable
- Proposed implementation (if you have ideas)

---

## 🔧 Development Setup

1. **Fork and clone:**
```bash
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install pytest black flake8  # Dev dependencies
```

4. **Run tests:**
```bash
pytest tests/
```

---

## 📝 Coding Standards

### Python Style
- Follow PEP 8
- Use `black` for formatting: `black research_scanner/`
- Use `flake8` for linting: `flake8 research_scanner/`
- Add docstrings to all functions/classes
- Keep functions focused and small

### Template Style
- Use clear, descriptive topic names
- Add comments explaining domain-specific choices
- Test with actual scans before submitting
- Document any unusual threshold/lookback choices

### Commit Messages
```
type(scope): brief description

Longer explanation if needed.

- Bullet points for details
- Reference issues: Fixes #123
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
```
feat(templates): add electrical engineering template

fix(arxiv): handle rate limiting more gracefully

docs(README): add installation troubleshooting section
```

---

## 🧪 Testing

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_template_manager.py

# With coverage
pytest --cov=research_scanner tests/
```

### Writing Tests
- Add tests for new features
- Test edge cases
- Mock external API calls
- Aim for >80% coverage

### Manual Testing
For templates, always do end-to-end tests:
```bash
python setup_wizard.py  # Select your template
python run_scan.py      # Run actual scan
# Verify papers are relevant
```

---

## 📋 Pull Request Process

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**
- Write code
- Add tests
- Update documentation
- Run tests and linting

3. **Commit with clear messages:**
```bash
git add .
git commit -m "feat(templates): add neuroscience template"
```

4. **Push to your fork:**
```bash
git push origin feature/your-feature-name
```

5. **Open a Pull Request:**
- Clear title and description
- Link related issues
- Describe what you changed and why
- Show test results
- Add screenshots if relevant

6. **Respond to feedback:**
- Address review comments
- Push updates to the same branch
- Be open to suggestions

---

## 🎯 Template Contribution Guidelines

### Required Elements
```yaml
domain: "Clear Domain Name"
description: "What research this template tracks"
sources:
  arxiv:
    enabled: true/false
    categories: ["cat1", "cat2"]  # If enabled
  pubmed:
    enabled: true/false
    queries: ["query1", "query2"]  # If enabled
topics:
  - name: "Clear Topic Name"
    keywords: ["kw1", "kw2", "kw3"]  # At least 3
    weight: 1.0-1.5
relevance_threshold: 0.3-0.5  # Higher for precision
days_lookback: 7-14
max_papers_per_scan: 40-50
```

### Best Practices
- **Keywords:** Use terms researchers actually search for
- **Weights:** 1.5 for core topics, 1.0 for supporting topics
- **Threshold:** 0.3-0.35 for broad fields, 0.4-0.5 for specialized
- **Lookback:** 7 days for fast-moving fields, 14+ for slower
- **Sources:** Only enable sources with relevant papers

### Testing Your Template
1. Run a scan: `python run_scan.py`
2. Check relevance: Are >70% of papers on-topic?
3. Check sources: Are the right sources being used?
4. Check papers: Sample 10 papers - are they useful?
5. Adjust if needed, repeat

---

## ❓ Questions?

- 💬 [GitHub Discussions](https://github.com/yourusername/research-scanner/discussions)
- 📧 Email: your.email@example.com
- 🐛 [Issue Tracker](https://github.com/yourusername/research-scanner/issues)

---

## 🙏 Recognition

Contributors will be:
- Listed in README
- Credited in release notes
- Recognized in project documentation

**Thank you for helping make research discovery better for everyone!** 🚀
