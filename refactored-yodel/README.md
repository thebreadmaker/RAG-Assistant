# Refactored YodeL - Complete Setup & Reboot Guide

## Part 1: Initial Setup (First Time Only)

### Prerequisites
- GitHub Codespaces environment active
- Python 3.12+ pre-installed in Codespaces
- Git repository cloned
- ~5-10 minutes for initial setup

---

## Section 1.1: Clone & Initial Configuration

### Step 1: Clone Repository
```bash
git clone <your-repo-url>

cd refactored-yodel
```

### Step 2: Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
cd refactored-yodel
cd backend
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed fastapi==0.104.1 uvicorn[standard]==0.24.0 ...
```

### Step 4: Setup Environment Variables
```bash
cd backend
cp .env.example .env
```

**Edit `.env` file:**
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# LLM Configuration (Local Ollama via ngrok)
OLLAMA_HOST=https://YOUR_NGROK_URL
OLLAMA_MODEL=llama3.2:3b

# Cache Configuration
CUSTOMER_CACHE_TTL=86400
QUERY_CACHE_TTL=1800

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

Replace `YOUR_NGROK_URL` with your actual ngrok forwarding URL.

---

## Section 1.2: Start Docker Services

### Step 1: Start Redis in Background
```bash
# From project root
docker-compose up -d
```

**Verify:**
```bash
docker ps
```

You should see `refactored-yodel-redis` container running.

### Step 2: Test Redis Connection
```bash
docker exec refactored-yodel-redis redis-cli ping
```

**Expected:** `PONG`

---

## Section 1.3: Setup RAG System

### Step 1: Initialize RAG
```bash
cd backend
python3 setup_rag.py
```

**What this does:**
- Creates necessary directories for vector database
- Downloads embedding model (~100MB, one-time only)
- Ingests documents from `memory/` folder
- Creates Chroma vector database

**Expected output:**
```
🚀 Setting up NCBA Safina RAG System...

📁 Creating directory structure...
✅ Created: backend/departments/retail_digital/memory

📥 Downloading embedding model (this may take a minute)...
✅ Embedding model ready

📚 Found 2 files in memory folder
📚 Ingesting documents...
✅ Ingested 42 document chunks

🔍 Verifying setup...
✅ Retrieval system working (5 results)

✨ Setup complete!
```

---

## Section 1.4: Start Backend API

### Step 1: Run Backend Server
```bash
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     Uvicorn restarting due to file changes...
```

### Step 2: Test Backend Health (New Terminal)
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "redis": true,
  "ollama": true
}
```

If `"ollama": false`, verify your ngrok connection is active.

---

## Section 1.5: Setup Frontend

### Step 1: Install Frontend Dependencies
```bash
# New terminal
cd frontend
npm install
```

### Step 2: Start Frontend Dev Server
```bash
npm run dev
```

**Expected output:**
```
  VITE v5.0.8  ready in 245 ms

  ➜  Local:   http://localhost:5173/
```

---

## Section 1.6: Verify Full Stack

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

### Test 2: Ask a Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital What is LFA?"}'
```

### Test 3: Access Frontend
Open Codespaces port preview on port 5173 (or use the local URL)

---

## Part 2: Reboot Guide (After Initial Setup)

Use this whenever you want to restart the system after it's already been installed.

---

## Section 2.1: Activate Environment & Start Docker

### Step 1: Activate Virtual Environment
```bash
cd refactored-yodel
source venv/bin/activate
```

### Step 2: Start Docker Services
```bash
docker-compose up -d
```

### Step 3: Verify Docker Services
```bash
docker ps
```

You should see `refactored-yodel-redis` running.

---

## Section 2.2: Start Backend (Single Command)
d
```bash
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```  

That's it! The backend will:
- ✅ Connect to Redis automatically
- ✅ Load all configuration from `.env`
- ✅ Initialize vector database
- ✅ Connect to Ollama via ngrok

**Keep this terminal open.**

---

## Section 2.3: Start Frontend (New Terminal)

```bash 
cd frontend 
npm run dev
```

**The system is now ready!**

---

## Quick Reboot Checklist

- [ ] Activate venv: `source venv/bin/activate`
- [ ] Start Docker: `docker-compose up -d`
- [ ] Start backend: `cd backend && python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] Start frontend: `cd frontend && npm run dev` (new terminal)
- [ ] Verify: `curl http://localhost:8000/health`

---

## Troubleshooting

### Issue: "Redis connection refused"
```bash
# Check if Redis is running
docker ps

# If not running, start it
docker-compose up -d

# Test connection
docker exec refactored-yodel-redis redis-cli ping
```

### Issue: "Ollama: false" in health check
```bash
# Verify ngrok is forwarding on Windows machine
curl https://YOUR_NGROK_URL/api/tags

# If not working, ensure:
# 1. Ollama is running on Windows
# 2. ngrok is running with correct command
# 3. Update OLLAMA_HOST in .env with correct ngrok URL
```

### Issue: Backend won't start
```bash
# Check port 8000 isn't in use
lsof -i :8000

# Kill if needed
kill -9 <PID>

# Restart backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: "Module not found" errors
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Frontend shows "Cannot reach backend"
```bash
# Verify backend is running and healthy
curl http://localhost:8000/health

# Check frontend proxy configuration in vite.config.js
# Should have:
# proxy: {
#   '/api': {
#     target: 'http://localhost:8000'
#   }
# }
```

---

## File Structure Reference

```
refactored-yodel/
├── backend/
│   ├── api/
│   │   ├── main.py           # FastAPI app entry point
│   │   └── schemas.py         # Request/response models
│   ├── core/
│   │   ├── cache.py           # Redis caching
│   │   ├── config.py          # Settings
│   │   ├── logger.py          # Logging setup
│   │   └── router.py          # Query routing
│   ├── departments/
│   │   └── retail_digital/
│   │       ├── memory/        # Document ingestion source
│   │       ├── db/            # Vector database
│   │       └── modules/
│   │           ├── general/   # RAG system
│   │           └── lfa/       # Eligibility checking
│   ├── .env                   # Environment variables
│   ├── setup_rag.py           # RAG initialization
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
├── logs/                      # System logs
├── docker-compose.yml         # Docker services
├── venv/                      # Python virtual environment
└── README.md
```

---

## Environment Variables Explained

| Variable | Purpose | Example |
|----------|---------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `OLLAMA_HOST` | Ollama LLM endpoint | `https://your-ngrok-url` |
| `OLLAMA_MODEL` | Model to use | `llama3.2:3b` |
| `API_HOST` | Backend listen address | `0.0.0.0` |
| `API_PORT` | Backend listen port | `8000` |
| `CUSTOMER_CACHE_TTL` | Customer data cache lifetime (seconds) | `86400` (24h) |
| `QUERY_CACHE_TTL` | Query result cache lifetime (seconds) | `1800` (30m) |

---

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8000 | `http://localhost:8000` |
| Frontend | 5173 | `http://localhost:5173` |
| Redis | 6379 | `localhost:6379` (internal) |
| API Docs | 8000 | `http://localhost:8000/docs` |

---

## Common Commands

### View Logs
```bash
# Backend startup log
cd backend
tail -f ../logs/all_*.log

# Monitor in real-time
python3 ../analyze_logs.py ../logs/all_*.log --query "ERROR"
```

### Stop Everything
```bash
# Stop backend (Ctrl+C in terminal)
# Stop frontend (Ctrl+C in terminal)

# Stop Docker services
docker-compose down

# Deactivate venv
deactivate
```

### Fresh Start (Clean State)
```bash
# Stop everything
docker-compose down
deactivate

# Restart fresh
source venv/bin/activate
docker-compose up -d
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Test API Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Ask a Question:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital What is LFA?"}'
```

**Ingest Documents:**
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json"
```

---

## Performance Tips

1. **First-time queries are slow** - LLM inference takes 10-30 seconds depending on model
2. **Responses are cached** - Same queries within 30 minutes hit the cache (instant)
3. **Use smaller models** - `tinyllama` is faster but less accurate than `llama3.2:3b`
4. **Monitor resources** - Check Docker memory usage with `docker stats`

---

## Next Steps

1. Add documents to `backend/departments/retail_digital/memory/`
2. Re-run ingest: `curl -X POST http://localhost:8000/api/ingest`
3. Query the system via frontend or API
4. Check logs in `logs/` directory for debugging

**Happy coding!** 🚀