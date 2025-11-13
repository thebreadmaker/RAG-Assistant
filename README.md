# Personal Assistant - Complete Setup Guide

This guide assumes you've just cloned the repository and are working in GitHub Codespaces (or a similar Linux environment).

---

## 📋 Prerequisites

Before starting, ensure you have:
- Python 3.9+
- Node.js 18+
- Redis (we'll install via Docker)
- Ollama (for LLM inference)

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