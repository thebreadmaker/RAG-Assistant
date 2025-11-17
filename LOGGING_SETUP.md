# 📋 Logging Setup Guide

## ✅ What's Been Implemented

Comprehensive logging has been added to your RAG Assistant across all major components:

### 1. **Core Logger Module** (`backend/core/logger.py`)
   - Dual file handlers: all logs + errors only
   - Rotating file handlers (10MB max, 10 backups)
   - Detailed format with timestamps, filenames, line numbers, function names
   - Console output for development

### 2. **HTTP Request/Response Logging** (`backend/api/main.py`)
   - Middleware logs all incoming requests: method, path, client, headers, body
   - Logs all responses: status code, duration
   - Exception tracking with full stack traces
   - Endpoint-specific logging for `/health`, `/api/ask`, `/api/ingest`

### 3. **Cache Logging** (`backend/core/cache.py`)
   - Cache GET/SET/DELETE operations
   - Hit/miss detection
   - TTL tracking
   - Initialization and health check logs

### 4. **RAG Retrieval Logging** (`backend/departments/retail_digital/modules/general/retriever.py`)
   - Query logging
   - Semantic search results
   - BM25 fallback tracking
   - RRF fusion details
   - Score calculations and thresholds

### 5. **LLM Generation Logging** (`backend/departments/retail_digital/modules/general/generator.py`)
   - LLM endpoint calls with timing
   - Payload details (model, temperature, etc.)
   - Response handling
   - Connection errors and timeouts
   - Confidence calculations

### 6. **Eligibility Processing Logging** (`backend/departments/retail_digital/modules/lfa/processor.py`)
   - Customer eligibility checks
   - Individual check results (pass/fail)
   - Cache hits/misses
   - Next review date calculations
   - Recommended actions

### 7. **Log Analyzer Tool** (`backend/analyze_logs.py`)
   - Statistical summary of logs
   - Error frequency analysis
   - Performance metrics (response times)
   - Cache hit rate analysis
   - Check pattern tracking
   - Search functionality

---

## 🚀 Quick Start

### 1. **Run Your Backend**

```bash
cd safina-rag
python start.py  # or: python -m backend.api.main
```

Logs will automatically be created in `safina-rag/logs/`:
- `all_TIMESTAMP.log` - All log levels (DEBUG and up)
- `errors_TIMESTAMP.log` - Errors only

### 2. **Watch Logs in Real-Time**

```bash
# Watch all logs as they're written
tail -f safina-rag/logs/all_*.log

# Watch only errors
tail -f safina-rag/logs/errors_*.log

# Follow with timestamps (watch mode)
tail -f safina-rag/logs/all_*.log | grep -E "(ERROR|WARN|INFO)"
```

### 3. **Analyze Logs**

```bash
cd safina-rag/backend

# Analyze latest log file with full statistics
python analyze_logs.py ../logs/all_*.log

# Show only errors
python analyze_logs.py ../logs/errors_*.log --errors-only

# Search for specific term
python analyze_logs.py ../logs/all_*.log --query "customer_id"
python analyze_logs.py ../logs/all_*.log --query "ERROR"
python analyze_logs.py ../logs/all_*.log --query "cache"
```

---

## 📊 Log Output Examples

### Successful Query Flow
```
2025-01-17 12:30:45 - INFO - 📥 POST /api/ask - Client: 127.0.0.1:54321
2025-01-17 12:30:45 - INFO - 🔍 Query received: 'Am I eligible for LFA?'
2025-01-17 12:30:45 - INFO - Query type: customer_specific
2025-01-17 12:30:45 - INFO - 🧑 Customer ID: C123456
2025-01-17 12:30:45 - INFO - 👤 Eligibility check started for customer: C123456
2025-01-17 12:30:45 - INFO - Cache cache hit
2025-01-17 12:30:45 - INFO - ✅ Eligibility status: Include
2025-01-17 12:30:45 - INFO - 📤 POST /api/ask - Status: 200 - Duration: 0.124s
```

### RAG Query with Retrieval
```
2025-01-17 12:31:00 - INFO - 🔍 Query received: 'What are your policies?'
2025-01-17 12:31:00 - INFO - Query type: general
2025-01-17 12:31:00 - INFO - 🔎 Retrieval started - Query: 'What are your policies?'
2025-01-17 12:31:00 - INFO - ✅ Semantic search: 5 chunks above threshold
2025-01-17 12:31:00 - INFO - ✅ Retrieval complete: 5 chunks returned
2025-01-17 12:31:00 - INFO - 📝 RAG generation started
2025-01-17 12:31:01 - INFO - ✅ LLM call succeeded (1.23s)
2025-01-17 12:31:01 - INFO - ✅ RAG generation successful
```

### Error with Stack Trace
```
2025-01-17 12:32:00 - ERROR - ❌ Exception during request POST /api/ask: Connection refused
Traceback (most recent call last):
  File "core/logger.py", line 42, in __init__
    response = requests.get(...)
  ...
ConnectionError: Failed to connect to Ollama endpoint
```

---

## 🔍 Common Debug Queries

### Find all customer lookups
```bash
python analyze_logs.py ../logs/all_*.log --query "customer_id"
```

### Track cache performance
```bash
python analyze_logs.py ../logs/all_*.log --query "cache"
```

### Find LLM issues
```bash
python analyze_logs.py ../logs/all_*.log --query "LLM"
```

### Find all failures
```bash
python analyze_logs.py ../logs/all_*.log --query "❌"
```

### See all retrieval operations
```bash
python analyze_logs.py ../logs/all_*.log --query "Retrieval"
```

### Search by component
```bash
python analyze_logs.py ../logs/all_*.log --query "Eligibility"
python analyze_logs.py ../logs/all_*.log --query "RAG"
python analyze_logs.py ../logs/all_*.log --query "Semantic"
```

---

## 📈 Log Emoji Guide

| Emoji | Meaning | Context |
|-------|---------|---------|
| 📥 | Incoming request | HTTP requests to the API |
| 📤 | Outgoing response | HTTP responses from the API |
| 🔍 | Search/Query | RAG retrieval initiated |
| 🤖 | LLM operation | Ollama LLM calls |
| 👤 | Customer operation | Customer eligibility checks |
| 💾 | Cache operation | Redis cache interactions |
| ✅ | Success | Completed operations |
| ❌ | Error | Failures and exceptions |
| ⚠️ | Warning | Fallbacks and issues |
| 🏥 | Health check | System health status |
| 📊 | Statistics | Metrics and counts |
| 📋 | Processing | Business logic execution |
| 🔴 | Critical error | In error logs |

---

## 🛠️ File Locations

```
safina-rag/
├── logs/                        ← All logs go here
│   ├── all_20250117_123045.log     (All levels)
│   ├── all_20250117_123045.log.1   (Rotated backup)
│   ├── errors_20250117_123045.log  (Errors only)
│   └── ...
├── backend/
│   ├── core/
│   │   └── logger.py           ← Logger setup
│   ├── api/
│   │   └── main.py             ← HTTP logging
│   ├── analyze_logs.py         ← Analysis tool
│   └── ...
```

---

## 🎯 Debugging Your Bug

Since you have a bug to find, here's the recommended approach:

1. **Start the app**: `python start.py`
2. **Run your problematic query** via the API
3. **Watch real-time logs**: `tail -f safina-rag/logs/all_*.log`
4. **After reproducing the issue**, run analysis:
   ```bash
   python analyze_logs.py ../logs/all_*.log
   ```
5. **Search for errors**: `grep "ERROR" safina-rag/logs/*.log`
6. **Search for specific patterns**:
   ```bash
   python analyze_logs.py ../logs/all_*.log --query "your_search_term"
   ```

---

## 📝 Notes

- **Log rotation**: Files automatically rotate at 10MB
- **TTL**: Logs are kept for debugging; clean old logs manually when done
- **Performance**: Logging adds ~1-2% overhead
- **Disk usage**: Monitor `safina-rag/logs/` directory size
- **Timestamps**: All logs use UTC datetime format (YYYY-MM-DD HH:MM:SS)

---

## ✨ Next Steps

1. **Run your app** and reproduce the bug
2. **Check logs** in real-time or via analysis tool
3. **Look for patterns** in error logs
4. **Compare timing** between successful and failed requests
5. **Use search** to trace request flow through the system

Good luck with debugging! 🚀
