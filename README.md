# NCBA Safina RAG Assistant

A production-ready Retrieval-Augmented Generation (RAG) system for NCBA Bank's customer service. Combines semantic search, BM25 keyword matching, and LLM generation to answer customer queries about eligibility, policies, and products.

## 🎯 Features

- **Hybrid Retrieval**: Semantic search + BM25 with Reciprocal Rank Fusion
- **Customer Eligibility**: LFA loan eligibility assessment with rule-based checks
- **Caching**: Redis-backed caching for performance optimization
- **Extensive Logging**: Detailed logs for debugging (all calls, responses, errors)
- **REST API**: FastAPI backend with CORS support
- **React Frontend**: Modern UI for chat interactions
- **Docker Support**: Easy deployment with Docker Compose

## 📋 Prerequisites

- **Docker** & **Docker Compose** (for Redis, Ollama)
- **Python 3.10+**
- **Node.js 16+** (for frontend)
- **4GB+ RAM** (for embeddings model and LLM)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd /workspaces/RAG-Assistant/safina-rag
```

### 2. Start Infrastructure (Redis + Ollama)

```bash
docker-compose up -d
```

Check services are running:
```bash
docker-compose ps
```

Wait for Ollama to be ready:
```bash
curl http://localhost:11434/api/tags
```

### 3. Backend Setup

#### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Initialize RAG System

Run the setup script to download embedding models and prepare directories:

```bash
python setup_rag.py
```

This will:
- ✅ Create necessary directories (`memory/`, `db/`)
- ✅ Download the embedding model (sentence-transformers/all-MiniLM-L6-v2)
- ✅ Prepare the system for document ingestion

#### Start Backend Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

**API Health Check:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": true,
  "ollama": true
}
```

### 4. Frontend Setup

Open a new terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## 📚 Document Ingestion

### Add Documents

Place your documents in the memory folder:

```bash
safina-rag/backend/departments/retail_digital/memory/
├── faqs.md           # FAQ documents
├── policies.md       # Policy documents
└── other-docs.md     # Any markdown/text files
```

### Ingest Documents

After adding or updating documents, run the ingest endpoint:

```bash
curl -X POST http://localhost:8000/api/ingest
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Ingested documents successfully. Total chunks: 245"
}
```

**Check ingestion logs:**
```bash
tail -f logs/all_*.log | grep -i ingest
```

## 💬 Using the API

### Query Example (General)

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital what is the LFA loan?"}'
```

**Response:**
```json
{
  "answer": "The LFA loan is a type of unsecured loan...",
  "metadata": {
    "sources": ["faqs.md"],
    "confidence": "high",
    "num_chunks": 5
  },
  "query_info": {
    "type": "general",
    "department": "retail_digital"
  }
}
```

### Query Example (Customer-Specific)

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "customer 12345 what is my eligibility for LFA?"}'
```

**Response:**
```json
{
  "answer": "Based on your profile, you are eligible...",
  "metadata": {
    "overall_status": "Include",
    "checks": {...},
    "next_review_date": "2025-12-17"
  },
  "query_info": {
    "type": "customer_specific",
    "customer_id": "12345"
  }
}
```

## 📊 Logging & Debugging

### Log Files

Logs are automatically created in `safina-rag/logs/`:

- `all_TIMESTAMP.log` - All events (DEBUG level)
- `errors_TIMESTAMP.log` - Errors only

### Watch Logs in Real-Time

```bash
tail -f safina-rag/logs/all_*.log
```

### Analyze Logs

Use the built-in log analyzer:

```bash
cd backend
python analyze_logs.py ../logs/all_*.log
```

**Analyze errors only:**
```bash
python analyze_logs.py ../logs/all_*.log --errors-only
```

**Search for specific term:**
```bash
python analyze_logs.py ../logs/all_*.log --query "customer_id"
python analyze_logs.py ../logs/all_*.log --query "ERROR"
```

### Log Output Includes

- ✅ HTTP requests/responses with timing
- ✅ Cache hits/misses
- ✅ RAG retrieval steps (semantic, BM25, fusion)
- ✅ LLM calls with model info
- ✅ Eligibility check results
- ✅ All errors with stack traces

## 🔧 Configuration

### Environment Variables

Create `.env` in `safina-rag/backend/`:

```env
# API
API_HOST=0.0.0.0
API_PORT=8000

# Ollama (LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral

# Redis (Cache)
REDIS_URL=redis://localhost:6379/0

# Query Config
TOP_K=5
SIMILARITY_THRESHOLD=0.5
QUERY_CACHE_TTL=3600
CUSTOMER_CACHE_TTL=86400
```

### core/config.py

All configuration is managed in `backend/core/config.py`. Values are loaded from `.env` or use defaults.

## 📁 Project Structure

```
safina-rag/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app with endpoints
│   │   └── schemas.py           # Pydantic models
│   ├── core/
│   │   ├── logger.py            # Logging configuration
│   │   ├── config.py            # Settings management
│   │   ├── cache.py             # Redis cache wrapper
│   │   ├── router.py            # Query classification
│   │   └── vector_manager.py    # Chroma vector DB
│   ├── departments/
│   │   └── retail_digital/
│   │       ├── modules/
│   │       │   ├── general/     # RAG (retriever, generator)
│   │       │   └── lfa/         # LFA eligibility processor
│   │       ├── memory/          # Document storage
│   │       │   ├── faqs.md
│   │       │   └── policies.md
│   │       └── db/              # Vector DB storage
│   ├── setup_rag.py             # Initialization script
│   ├── requirements.txt         # Python dependencies
│   └── analyze_logs.py          # Log analysis tool
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── context/             # Theme context
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── logs/                        # Auto-generated logs
│   ├── all_*.log
│   └── errors_*.log
│
├── docker-compose.yml           # Redis + Ollama services
└── README.md                    # This file
```

## 🔄 RAG Pipeline

### Query Flow

```
User Query
    ↓
[Query Classification] → Classify as "general" or "customer_specific"
    ↓
IF customer_specific:
    ├─ Extract customer ID
    ├─ Load customer data
    ├─ Run eligibility checks
    └─ Generate response
    ↓
IF general OR (customer_specific but no ID found):
    ├─ Retrieve documents [Semantic Search]
    ├─ Filter by similarity threshold
    ├─ If poor results → Use BM25 fallback
    ├─ Fuse results (RRF)
    ├─ Call LLM with context
    └─ Generate answer
    ↓
Return Response
```

### Hybrid Retrieval Details

1. **Semantic Search**: Using sentence-transformers embeddings
2. **BM25 Fallback**: Keyword matching if semantic results are poor
3. **RRF Fusion**: Combines both with weights (semantic: 0.7, BM25: 0.3)
4. **Caching**: Results cached in Redis

## 🛑 Stopping the System

### Stop Backend

```bash
# In backend terminal
Ctrl + C
```

### Stop Frontend

```bash
# In frontend terminal
Ctrl + C
```

### Stop Infrastructure

```bash
docker-compose down
```

**Remove volumes (wipes all data):**
```bash
docker-compose down -v
```

## 📊 Monitoring

### Check Service Health

```bash
# Health check endpoint
curl http://localhost:8000/health

# Check Redis
redis-cli ping

# Check Ollama
curl http://localhost:11434/api/tags
```

### View Active Processes

```bash
# Backend
ps aux | grep uvicorn

# Frontend
ps aux | grep vite

# Docker services
docker-compose ps
```

## 🐛 Troubleshooting

### Backend Won't Start

**Error: "Connection refused" (Redis/Ollama)**
- Ensure Docker services are running: `docker-compose ps`
- Wait for services to be healthy: `docker-compose logs ollama`

**Error: "Module not found"**
- Install dependencies: `pip install -r requirements.txt`
- Run setup: `python setup_rag.py`

### Slow Queries

- Check cache hit rate: `python analyze_logs.py ../logs/all_*.log`
- Adjust `TOP_K` in config (higher = slower but better recall)
- Increase `SIMILARITY_THRESHOLD` to filter poor results faster

### Ingestion Fails

- Ensure documents exist in `memory/` folder
- Check logs: `tail -f logs/all_*.log | grep -i ingest`
- Run ingestion again: `curl -X POST http://localhost:8000/api/ingest`

### Frontend Can't Connect to API

- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/api/main.py`
- Verify frontend API URL is correct in code

## 📖 API Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

When making changes:
1. Update relevant modules
2. Re-run setup if dependencies change: `python setup_rag.py`
3. Re-ingest documents if FAQ/policy content changes: `curl -X POST http://localhost:8000/api/ingest`
4. Check logs for any errors: `python analyze_logs.py ../logs/all_*.log --errors-only`

## 📝 License

Internal NCBA Project

## 📞 Support

For issues or questions:
1. Check logs: `python analyze_logs.py ../logs/all_*.log`
2. Review configuration in `backend/core/config.py`
3. Verify all services are running: `docker-compose ps`

---

## 🚀 Step-by-Step Setup

### **1. Navigate to Project Directory**

```bash
cd safina-rag
```

---

### **2. Set Up Backend**

#### **2.1 Create Python Virtual Environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### **2.2 Install Python Dependencies**

```bash
pip install -r requirements.txt
```

#### **2.3 Configure Environment Variables**

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults should work for local development):
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Cache Configuration
CUSTOMER_CACHE_TTL=86400
QUERY_CACHE_TTL=1800

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

---

### **3. Set Up Infrastructure (Redis + Ollama)**

#### **3.1 Install Docker (if not already installed)**

```bash
# For Codespaces, Docker is pre-installed
docker --version
```

#### **3.2 Start Redis & Ollama with Docker Compose**

```bash
# Go back to project root
cd ..

# Start services
docker-compose up -d
```

This will start:
- **Redis** on port `6379`
- **Ollama** on port `11434`

#### **3.3 Download Ollama Model**

```bash
# Download the Llama 3.2 3B model (takes 2-3 minutes)
docker exec -it safina-ollama ollama pull llama3.2:3b
```

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

You should see JSON output with the model listed.

---

### **4. Ingest Documents into Vector Database**

#### **4.1 Run the Setup Script**

```bash
cd backend
python setup_rag.py
```

This script will:
1. Download embedding models (first time only)
2. Create necessary directories
3. Ingest documents from `backend/departments/retail_digital/memory/`
4. Build the vector database

**Expected output:**
```
🚀 Setting up NCBA Safina RAG System...
📁 Creating directory structure...
✅ Created: /path/to/backend/departments/retail_digital/memory
📥 Downloading embedding model...
✅ Embedding model ready
📚 Found 2 files in memory folder
📚 Ingesting documents...
✅ Ingested 145 document chunks
🔍 Verifying setup...
✅ Retrieval system working (5 results)
✨ Setup complete!
```

---

### **5. Start the Backend Server**

```bash
# Make sure you're in the backend directory
cd backend  # if not already there

# Activate venv if not active
source venv/bin/activate

# Start FastAPI server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify backend is running:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": true,
  "ollama": true
}
```

---

### **6. Set Up Frontend**

Open a **new terminal** (keep backend running):

#### **6.1 Install Frontend Dependencies**

```bash
cd safina-rag/frontend
npm install
```

#### **6.2 Start Frontend Dev Server**

```bash
npm run dev
```

**Expected output:**
```
VITE v5.0.8  ready in 324 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

---

### **7. Access the Application**

#### **Option A: Local Development**
Open your browser to: **http://localhost:3000**

#### **Option B: GitHub Codespaces**
Codespaces will automatically forward port `3000`. Click the popup or go to:
- **Ports** tab → Find port `3000` → Click the globe icon

---

## ✅ Verification Checklist

Run these checks to ensure everything is working:

### **1. Backend Health Check**
```bash
curl http://localhost:8000/health
```
✅ Should return `{"status":"healthy","redis":true,"ollama":true}`

### **2. Test Customer Query**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital check eligibility for 599741"}'
```

### **3. Test General Query**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital what is the LFA loan?"}'
```

### **4. Check Vector Database**
```bash
curl http://localhost:8000/api/ingest
```
✅ Should return `{"status":"success","message":"Ingested documents successfully. Total chunks: 145"}`

---

## 🎯 Usage Examples

### **In the UI:**

1. **Check Customer Eligibility:**
   ```
   @retail_digital why is customer 599741 excluded?
   ```

2. **Ask General Questions:**
   ```
   @retail_digital what are the eligibility requirements?
   ```

3. **Policy Questions:**
   ```
   @retail_digital what is the cooling period after clearing arrears?
   ```

---

## 🐛 Troubleshooting

### **Problem: Backend won't start**
```bash
# Check if ports are available
lsof -i :8000  # Backend
lsof -i :6379  # Redis
lsof -i :11434 # Ollama

# Restart Docker services
docker-compose restart
```

### **Problem: Ollama model not found**
```bash
# Re-download the model
docker exec -it safina-ollama ollama pull llama3.2:3b

# Verify model exists
docker exec -it safina-ollama ollama list
```

### **Problem: Vector database is empty**
```bash
cd backend
python setup_rag.py
```

### **Problem: Frontend can't connect to backend**
Check `frontend/vite.config.js` proxy settings:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

---

## 📂 Project Structure

```
safina-rag/
├── backend/
│   ├── api/                    # FastAPI endpoints
│   ├── core/                   # Core utilities (cache, router, vector DB)
│   ├── departments/
│   │   └── retail_digital/
│   │       ├── memory/         # Documents for RAG (FAQs, policies)
│   │       ├── modules/
│   │       │   ├── lfa/       # Customer eligibility module
│   │       │   └── general/   # RAG module
│   │       └── db/            # Vector database (generated)
│   ├── requirements.txt
│   └── setup_rag.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

---

## 🎉 You're All Set!

Your Safina RAG Assistant is now running:
- **Backend API:** http://localhost:8000
- **Frontend UI:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

Try asking questions about customer eligibility or bank policies! 🚀