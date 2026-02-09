# Scholar's Terminal - Quick Start Guide

## 🚀 Get Started in 5 Minutes

---

## Step 1: Verify Database (30 seconds)

The 108 GB ChromaDB database has been migrated. Let's verify it:

```bash
cd D:\Claude\Projects\ScholarsTerminal\backend
python
```

```python
import chromadb

client = chromadb.PersistentClient(
    path="D:/Claude/Projects/ScholarsTerminal/data/vector_db"
)

# Get collection
collection = client.get_collection("documents")

# Check count
print(f"Total documents: {collection.count():,}")
# Should show ~13 million chunks

# Test query
results = collection.query(
    query_texts=["artificial intelligence"],
    n_results=3
)

print(f"Sample results: {len(results['ids'][0])}")
```

**Expected Output:**
```
Total documents: 12,970,453
Sample results: 3
```

If this works, your database is perfect! ✅

---

## Step 2: Install Dependencies (5 minutes)

```bash
cd D:\Claude\Projects\ScholarsTerminal\backend
pip install -r requirements.txt
```

**Download spaCy model:**
```bash
python -m spacy download en_core_web_sm
```

---

## Step 3: Configure Environment (2 minutes)

Create `backend/.env`:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
PRIMARY_MODEL=llama3.2:latest
FALLBACK_MODEL=mistral:latest

# ChromaDB Path
CHROMA_DB_PATH=D:/Claude/Projects/ScholarsTerminal/data/vector_db

# Document Paths
BOOKS_PATH=D:/Books
GITHUB_PATH=D:/GitHub

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Voice Settings
ENABLE_VOICE=true
VOICE_LANGUAGE=en-US
```

---

## Step 4: Start Backend (30 seconds)

```bash
cd D:\Claude\Projects\ScholarsTerminal\backend
uvicorn knowledge_chatbot:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Test API:** Open `http://localhost:8000/docs` in browser

---

## Step 5: Setup Frontend (3 minutes)

**Terminal 2:**
```bash
cd D:\Claude\Projects\ScholarsTerminal\frontend
npm install
npm run dev
```

**Access:** Open `http://localhost:5173`

---

## 🎯 Quick Test Query

Once both are running:

1. Open `http://localhost:5173`
2. Type: **"What does Feynman say about quantum mechanics?"**
3. Press Enter

You should get:
- Relevant passages from your books
- Source citations
- Response time: 5-10 seconds

---

## 🔍 Alternative: Command Line Test

```bash
cd backend
python
```

```python
from core.chatbot import KnowledgeChatbot

# Initialize
chatbot = KnowledgeChatbot()

# Query
response = chatbot.query("What is machine learning?")

print(response['answer'])
print(f"\nSources: {response['sources']}")
```

---

## 🐛 Troubleshooting

### Issue: "ChromaDB not found"

```bash
# Check database exists
dir "D:\Claude\Projects\ScholarsTerminal\data\vector_db"
```

If empty, the database is still copying. Wait for completion.

### Issue: "Ollama model not found"

```bash
# List models
ollama list

# Pull missing model
ollama pull llama3.2:latest
```

### Issue: "Module not found"

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Port already in use"

```bash
# Change port in command
uvicorn knowledge_chatbot:app --reload --port 8001
```

---

## 📊 Verify Everything Works

**Quick Health Check Script:**

Create `backend/health_check.py`:
```python
#!/usr/bin/env python3
import sys
import chromadb
import requests

def check_database():
    try:
        client = chromadb.PersistentClient(
            path="D:/Claude/Projects/ScholarsTerminal/data/vector_db"
        )
        collection = client.get_collection("documents")
        count = collection.count()
        print(f"✅ Database OK: {count:,} documents")
        return True
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False

def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama OK: {len(models)} models available")
            return True
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return False

def check_api():
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API OK: Server responding")
            return True
    except Exception as e:
        print(f"⚠️  API not running (start with uvicorn)")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Scholar's Terminal - Health Check")
    print("=" * 50)
    
    db_ok = check_database()
    ollama_ok = check_ollama()
    api_ok = check_api()
    
    print("=" * 50)
    
    if db_ok and ollama_ok:
        print("✅ System Ready!")
        sys.exit(0)
    else:
        print("❌ System has issues")
        sys.exit(1)
```

**Run it:**
```bash
python backend/health_check.py
```

---

## 🎓 Common Workflows

### Query Your Books
```python
query = "What does Richard Feynman say about learning?"
# System searches your 9,000+ books
```

### Search Code
```python
query = "FastAPI authentication examples"
# System searches your GitHub repos
```

### Mixed Query
```python
query = "How to implement RAG system with ChromaDB?"
# System searches both books (theory) and code (examples)
```

---

## 📁 Important Paths

| What | Path |
|------|------|
| Backend Code | `D:\Claude\Projects\ScholarsTerminal\backend` |
| Frontend Code | `D:\Claude\Projects\ScholarsTerminal\frontend` |
| Database | `D:\Claude\Projects\ScholarsTerminal\data\vector_db` |
| Config | `backend\.env` |
| Logs | `backend\logs\` |

---

## 🔄 Daily Usage

**Start Backend:**
```bash
cd D:\Claude\Projects\ScholarsTerminal\backend
uvicorn knowledge_chatbot:app --reload
```

**Start Frontend:**
```bash
cd D:\Claude\Projects\ScholarsTerminal\frontend
npm run dev
```

**Or create batch file `start.bat`:**
```batch
@echo off
start cmd /k "cd /d D:\Claude\Projects\ScholarsTerminal\backend && uvicorn knowledge_chatbot:app --reload"
start cmd /k "cd /d D:\Claude\Projects\ScholarsTerminal\frontend && npm run dev"
echo Scholar's Terminal starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
```

---

## 📈 Next Steps

1. ✅ Verify database (Step 1)
2. ✅ Install dependencies (Step 2)
3. ✅ Configure environment (Step 3)
4. ✅ Start backend (Step 4)
5. ✅ Start frontend (Step 5)
6. ✅ Test queries
7. 🎯 Start using your 13 million document knowledge base!

---

## 💡 Pro Tips

- **Voice Mode**: Enable in settings for hands-free queries
- **Keyboard Shortcuts**: `Ctrl+K` to focus search
- **Source View**: Click sources to see original text
- **Export**: Save conversations for later reference
- **API**: Use `/docs` endpoint for API exploration

---

## 🎉 You're Ready!

Your Scholar's Terminal is now fully operational with:
- ✅ 13 million document chunks
- ✅ 108 GB vector database
- ✅ GitHub code search
- ✅ Voice capabilities
- ✅ Clean, organized structure

**Start querying your personal library!** 🚀

---

**Last Updated**: January 8, 2025  
**Status**: ✅ Production Ready  
**Migration**: Complete
