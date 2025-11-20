# Refactored YodeL

Welcome to Refactored YodeL, an advanced Retrieval-Augmented Generation (RAG) assistant for document-based Q&A, analytics, and automation.

## Project Overview
Refactored YodeL combines semantic search, hybrid retrieval, and LLM-powered answer generation. It supports interactive orchestration, monitoring, and extensive logging for robust troubleshooting and analytics.

## Features
- FastAPI backend with custom logging
- Chroma vector DB, Redis cache, Ollama LLM
- Document ingestion and hybrid retrieval pipeline
- Interactive shell scripts for orchestration and monitoring
- Log analyzer tool for debugging
- Frontend chat interface (Vite + React)

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js (for frontend)

### 1. Clone & Install
```bash
# Clone the repository
# (Already done)

# Install Python dependencies
cd refactored-yodel/backend
pip install -r requirements.txt
```

### 2. Start Services
```bash
# From the scripts directory
cd refactored-yodel/scripts
./boot.sh
```

- This will start all backend services, pull models, and ingest documents automatically.
- Use `--stop` or `--restart` interactively in the boot or monitor scripts.

### 3. Frontend Setup
```bash
cd refactored-yodel/frontend
npm install
npm run dev
```

### 4. Monitoring & Logs
- Monitor system activity: `./monitor.sh` (in scripts)
- Logs are stored in `refactored-yodel/logs/`
- Analyze logs: `python backend/analyze_logs.py`

## Project Structure
```
refactored-yodel/
  backend/        # FastAPI, core logic, ingestion, logging
  frontend/       # Vite + React chat interface
  scripts/        # Orchestration and monitoring scripts
  logs/           # All system logs
```

## Branding
- Project name: **Refactored YodeL** (spelled exactly)
- All references to previous names have been updated.

## Support
For issues, troubleshooting, or feature requests, please open an issue or contact the maintainer.
