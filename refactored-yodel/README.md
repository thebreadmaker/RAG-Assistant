# **Refactored YodeL – Complete Setup Guide**

A streamlined walkthrough for setting up Refactored YodeL in GitHub Codespaces or any Linux-based development environment.
This guide assumes you’ve freshly cloned the repository and are preparing both the backend and frontend for local development.

---

## **📦 Prerequisites**

Make sure the following are available in your environment:

* **Python 3.9+**
* **Node.js 18+**
* **Redis** (runs via Docker)
* **Ollama** (LLM engine for embeddings + inference)
* **Docker & Docker Compose**

---

## **🚀 Full Setup Workflow**

### **1. Move Into the Project**

```bash
cd refactored-yodel
```

---

## **2. Backend Setup**

### **2.1 Create a Virtual Environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### **2.2 Install Dependencies**

```bash
pip install -r requirements.txt
```

### **2.3 Configure Environment Variables**

Copy example configuration:

```bash
cp .env.example .env
```

Default configuration (modify only if necessary):

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Cache
CUSTOMER_CACHE_TTL=86400
QUERY_CACHE_TTL=1800

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## **3. Start Infrastructure (Redis + Ollama)**

### **3.1 Verify Docker Availability**

```bash
docker --version
```

### **3.2 Launch Services**

```bash
# Return to project root
cd ..

docker-compose up -d

# Alternatively
docker-compose -f refactored-yodel/docker-compose.yml up -d

```

This boots:

* **Redis** → `6379`
* **Ollama** → `11434`

### **3.3 Pull the Required Ollama Model**

```bash
docker exec -it refactored-yodel-ollama ollama pull llama3.2:3b
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

---

## **4. Ingest RAG Documents**

### **4.1 Run RAG Setup Script**

```bash
cd backend
python setup_rag.py
```

The script will:

* Download embedding models
* Build directory structure
* Index files from **departments/retail_digital/memory/**
* Generate the vector database

You should see a summary showing number of chunks ingested and confirmation that retrieval works.

---

## **5. Run the Backend API**

```bash
cd backend
source venv/bin/activate

python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Check service health:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "healthy",
  "redis": true,
  "ollama": true
}
```

---

## **6. Frontend Setup**

Open a **new terminal** while backend keeps running.

### **6.1 Install Dependencies**

```bash
cd refactored-yodel/frontend
npm install
```

### **6.2 Start Dev Server**

```bash
npm run dev
```

You’ll see a development URL such as:

```
Local: http://localhost:3000/
```

---

## **7. Access the Application**

### **Local**

Open: **[http://localhost:3000](http://localhost:3000)**

### **Codespaces**

Use the **Ports** tab → expose port 3000 → click the globe icon.

---

# **✅ System Verification Checklist**

### **1. API health**

```bash
curl http://localhost:8000/health
```

### **2. Customer query**

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital check eligibility for 599741"}'
```

### **3. General knowledge query**

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "@retail_digital what is the LFA loan?"}'
```

### **4. Check ingestion status**

```bash
curl http://localhost:8000/api/ingest
```

---

# **🎯 Usage Examples**

Inside the UI:

### **Check a customer’s status**

```
@retail_digital why is customer 599741 excluded?
```

### **Ask policy or process questions**

```
@retail_digital what are the eligibility requirements?
```

### **Clarify specific rules**

```
@retail_digital what is the cooling period after arrears clearance?
```

---

# **🐛 Troubleshooting**

### **Backend not starting**

```
lsof -i :8000
lsof -i :6379
lsof -i :11434

docker-compose restart
```

### **Model missing**

```
docker exec -it refactored-yodel-ollama ollama pull llama3.2:3b
docker exec -it refactored-yodel-ollama ollama list
```

### **Vector DB is empty**

```
cd backend
python setup_rag.py
```

### **Frontend failing to reach backend**

Check `frontend/vite.config.js`:

```js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

---

# **📁 Project Structure**

```
refactored-yodel/
│
├── backend/
│   ├── api/                 # FastAPI endpoints
│   ├── core/                # Cache, retrieval, database
│   ├── departments/
│   │   └── retail_digital/
│   │       ├── memory/      # RAG source documents
│   │       ├── modules/     # Customer eligibility + general modules
│   │       └── db/          # Vector database
│   ├── requirements.txt
│   └── setup_rag.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
└── docker-compose.yml
```

---

# **🎉 All Set!**

You now have a fully working Refactored YodeL Assistant:

* **Backend:** [http://localhost:8000](http://localhost:8000)
* **Frontend:** [http://localhost:3000](http://localhost:3000)
* **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

Start asking questions, checking eligibility, or exploring bank policy knowledge—your assistant is live.
