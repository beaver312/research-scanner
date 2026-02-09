# Integration Guide: Research Scanner → Scholars Terminal

## Quick Start

### 1. Copy files into your project
Copy the entire `research_scanner/` folder into your Scholars Terminal project:
```
D:\Claude\Projects\scholars-terminal\
├── research_scanner/          ← NEW: drop this folder here
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── summarizer.py
│   ├── indexer.py
│   ├── scanner.py
│   ├── scheduler.py
│   ├── api_routes.py
│   ├── requirements.txt
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base_source.py
│   │   ├── arxiv_source.py
│   │   ├── semantic_scholar_source.py
│   │   └── huggingface_source.py
│   └── tests/
│       ├── __init__.py
│       ├── test_scanner.py
│       └── test_integration.py
├── Scholars_api.py            ← existing backend
├── frontend/                  ← existing React frontend
└── data/
    └── vector_db/             ← existing ChromaDB
```

### 2. Install new dependency
```bash
pip install apscheduler
```
(chromadb, sentence-transformers, and fastapi should already be installed)

### 3. Add routes to Scholars_api.py

Add these lines to your existing `Scholars_api.py`:

```python
# Near the top, with other imports:
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "research_scanner"))
from research_scanner.api_routes import create_research_router
from research_scanner.scheduler import start_scheduler

# After creating the FastAPI app (after `app = FastAPI(...)`):
app.include_router(create_research_router(), prefix="/api/research")

# Optionally, start the background scheduler:
# (This will auto-scan daily at 3 AM and once on startup)
# scheduler = start_scheduler()
```

### 4. Test it

**CLI test (no server needed):**
```bash
cd D:\Claude\Projects\scholars-terminal\research_scanner
python scanner.py test-sources
```

**Run a manual scan:**
```bash
python scanner.py scan --verbose
```

**Via API (after starting the backend):**
```
GET  http://localhost:8000/api/research/status
GET  http://localhost:8000/api/research/latest
GET  http://localhost:8000/api/research/search?q=RAG
POST http://localhost:8000/api/research/scan
```

## Configuration

Edit `research_scanner/config.py` to customize:

- **Topics**: Add/remove research topics and keywords
- **Sources**: Enable/disable arXiv, Semantic Scholar, HuggingFace
- **Schedule**: Change scan frequency (default: daily at 3 AM)
- **Model**: Change which Ollama model is used for summarization
- **Threshold**: Adjust relevance_threshold (0.0-1.0) to control signal vs noise

## How It Works

```
                                    ┌────────────────┐
                                    │  Your Ollama   │
                                    │  (localhost:    │
                                    │   11434)        │
                                    └───────┬────────┘
                                            │
  ┌──────────┐   ┌──────────────┐   ┌──────▼────────┐   ┌──────────────┐
  │  arXiv   │──▶│              │──▶│  Summarizer   │──▶│  ChromaDB    │
  │  S2 API  │   │  Scanner     │   │  (2-pass:     │   │  "research_  │
  │  HF Daily│   │  Orchestrator│   │   relevance   │   │   papers"    │
  └──────────┘   │              │   │   + summary)  │   │  collection  │
                 └──────────────┘   └───────────────┘   └──────┬───────┘
                                                               │
                                                        ┌──────▼───────┐
                                                        │  FastAPI     │
                                                        │  /api/       │
                                                        │  research/*  │
                                                        └──────────────┘
```

1. **Fetch**: Scanner pulls papers from arXiv, Semantic Scholar, and HuggingFace
2. **Dedup**: Skips papers already in the database (tracked in scan_history.json)
3. **Score**: Quick keyword check + Ollama relevance scoring (0.0-1.0)
4. **Filter**: Papers below the threshold are skipped
5. **Summarize**: Ollama generates structured summaries for relevant papers
6. **Index**: Papers + summaries chunked and stored in ChromaDB
7. **Search**: Available via API and integrated with main Scholars Terminal chat

Papers indexed here will show up in your normal Scholars Terminal searches too,
since they live in the same ChromaDB instance.
