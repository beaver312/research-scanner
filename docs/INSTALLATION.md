# Installation Guide

Complete installation instructions for Research Scanner.

---

## Quick Install (5 minutes)

### Prerequisites

- **Python 3.8 or higher**
- **Git** (for cloning the repository)
- **~2GB disk space** (for dependencies and vector database)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install Ollama (Optional but Recommended)

Ollama provides AI summarization for papers.

**macOS/Linux:**
```bash
curl https://ollama.ai/install.sh | sh
ollama pull phi3:3.8b
```

**Windows:**
Download from [https://ollama.ai/](https://ollama.ai/)

**Alternative models:**
- `phi3:3.8b` - Fast, efficient (recommended)
- `qwen2.5:7b` - Slightly better quality
- `llama3.2:3b` - Smaller, faster

### Step 4: Run Setup Wizard

```bash
python setup_wizard.py
```

Follow the prompts to:
1. Choose your research domain
2. Configure sources
3. Set your preferences

### Step 5: Run Your First Scan

```bash
python run_scan.py
```

**Done!** Papers are now indexed in ChromaDB.

---

## Detailed Installation

### System Requirements

**Minimum:**
- Python 3.8+
- 4GB RAM
- 2GB disk space
- Internet connection

**Recommended:**
- Python 3.10+
- 8GB+ RAM (for large paper collections)
- SSD storage (faster ChromaDB operations)
- Stable internet (for API calls)

### Installation Methods

#### Method 1: pip install (Coming Soon)

```bash
pip install research-scanner
```

#### Method 2: From Source (Current)

```bash
# Clone repository
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup_wizard.py
```

#### Method 3: Development Install

```bash
# Clone with dev dependencies
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner

# Install in editable mode with dev tools
pip install -e .
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest
```

---

## Configuration

### Basic Configuration

The setup wizard creates `user_config.yaml`:

```yaml
domain: "AI & Machine Learning"
sources:
  arxiv:
    enabled: true
    categories: ["cs.AI", "cs.LG"]
  pubmed:
    enabled: true
    queries: ["machine learning healthcare"]
  huggingface:
    enabled: true
topics:
  - name: "Retrieval Augmented Generation"
    keywords: ["RAG", "retrieval", "context"]
    weight: 1.5
relevance_threshold: 0.3
days_lookback: 7
max_papers_per_scan: 50
```

### Advanced Configuration

Create `.env` file for API keys (optional):

```bash
# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:3.8b

# ChromaDB settings
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION=research_papers

# Logging
LOG_LEVEL=INFO
LOG_FILE=scanner.log
```

---

## Platform-Specific Instructions

### Windows

**1. Install Python:**
- Download from [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation

**2. Install Git:**
- Download from [git-scm.com](https://git-scm.com/)

**3. Install Visual C++ (for some dependencies):**
- Download [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**4. Run in PowerShell:**
```powershell
# Clone and install
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run setup
python setup_wizard.py
```

### macOS

**1. Install Homebrew (if not installed):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install Python:**
```bash
brew install python@3.11
```

**3. Clone and install:**
```bash
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup_wizard.py
```

### Linux (Ubuntu/Debian)

**1. Install dependencies:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

**2. Clone and install:**
```bash
git clone https://github.com/yourusername/research-scanner.git
cd research-scanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup_wizard.py
```

---

## Troubleshooting

### Common Issues

#### ImportError: No module named 'chromadb'

**Solution:**
```bash
pip install --upgrade chromadb
```

#### ChromaDB version conflicts

**Solution:**
```bash
pip uninstall chromadb
pip install chromadb>=0.4.0
```

#### Ollama connection refused

**Check Ollama is running:**
```bash
# Should show running models
ollama list

# If not running, start it
ollama serve
```

#### Papers not appearing

**Possible causes:**
1. All papers already indexed (try different domain)
2. Network issues (check internet connection)
3. API rate limits (wait a few minutes)

**Debug:**
```bash
# Check logs
cat scanner.log

# Run with verbose output
python run_scan.py --verbose
```

#### Permission errors on Windows

**Solution:**
Run PowerShell as Administrator or adjust execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Verification

### Test Your Installation

```bash
# Run example script
python examples/1_quick_start.py

# Should see:
# ✓ Template loaded
# ✓ Scanner configured
# ✓ Papers fetched
# ✓ ChromaDB indexed
```

### Check Components

```bash
# Python version
python --version  # Should be 3.8+

# Installed packages
pip list | grep -E "(chromadb|sentence-transformers|rich)"

# Ollama (if installed)
ollama list  # Should show models

# ChromaDB
ls chroma_db/  # Should exist after first scan
```

---

## Updating

### Update to Latest Version

```bash
cd research-scanner
git pull origin main
pip install -r requirements.txt --upgrade
```

### Migrate Data (if needed)

```bash
# Backup current database
cp -r chroma_db chroma_db.backup

# Update and re-index if needed
python run_scan.py --reindex
```

---

## Uninstallation

### Remove Software

```bash
# Delete repository
rm -rf research-scanner

# Remove virtual environment (if used)
rm -rf venv
```

### Keep Data

Your ChromaDB database is in `chroma_db/`. If you want to keep indexed papers:
```bash
cp -r research-scanner/chroma_db ~/backup_papers
```

---

## Next Steps

After installation:

1. **Run your first scan:**
   ```bash
   python run_scan.py
   ```

2. **Try different domains:**
   ```bash
   python setup_wizard.py  # Choose different template
   python run_scan.py
   ```

3. **Explore examples:**
   ```bash
   python examples/1_quick_start.py
   python examples/2_switching_domains.py
   ```

4. **Read documentation:**
   - [Template Guide](TEMPLATES.md)
   - [API Documentation](API.md)
   - [Contributing](../CONTRIBUTING.md)

---

## Getting Help

**Issues:**
- GitHub Issues: https://github.com/yourusername/research-scanner/issues
- Check existing issues first
- Provide error logs and system info

**Community:**
- Discussions: https://github.com/yourusername/research-scanner/discussions
- Ask questions
- Share templates
- Show what you've built

**Documentation:**
- README: Main project overview
- TEMPLATES.md: Creating custom templates
- API.md: API reference
- Examples: `examples/` directory

---

**Installation complete! Happy researching! 📚**
