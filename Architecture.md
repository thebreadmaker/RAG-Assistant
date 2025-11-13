# NCBA Personal Assistant - Architecture & Design Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)
7. [Security & Scalability](#security--scalability)
8. [API Reference](#api-reference)

---

## 1. System Overview

### 1.1 Purpose
The NCBA Personal Assistant is an intelligent conversational AI system designed to:
- Check customer loan eligibility based on predefined business rules
- Answer general queries about bank policies and loan products using document retrieval
- Provide natural language responses powered by a local LLM (Llama 3.2)

### 1.2 Key Features
- **Dual Query Processing**: Rule-based (customer eligibility) + RAG-based (general queries)
- **Semantic Query Routing**: Automatically classifies queries by intent and department
- **Hybrid Retrieval**: Combines semantic search (vector embeddings) with BM25 keyword matching
- **Intelligent Caching**: Redis-based caching for customer data and query results
- **Real-time Responses**: Fast, sub-second responses for most queries
- **Modular Architecture**: Extensible department and module system

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ ChatInterface│  │ MessageList  │  │  InputBox    │           │
│  └──────┬───────┘  └──────────────┘  └──────────────┘           │
│         │                                                       │
│         │ HTTP POST /api/ask                                    │
└─────────┼─────────────────────────────────────────────────────┬─┘
          │                                                     │
          ▼                                                     │
┌─────────────────────────────────────────────────────────────┐ │
│                    BACKEND (FastAPI)                        │ │
│                                                             │ │
│  ┌────────────────────────────────────────────────────┐     │ │
│  │              API Layer (main.py)                   │     │ │
│  │  - /api/ask     - /health     - /api/ingest        │     │ │
│  └────────────┬───────────────────────────────────────┘     │ │
│               │                                             │ │
│               ▼                                             │ │
│  ┌────────────────────────────────────────────────────┐     │ │
│  │         Core Layer (router.py)                     │     │ │
│  │  ┌─────────────────────────────────────────────┐   │     │ │
│  │  │  Query Router (Semantic Classification)     │   │     │ │
│  │  │  - Extract department tag (@retail_digital) │   │     │ │
│  │  │  - Extract customer ID (regex)              │   │     │ │
│  │  │  - Classify intent (customer vs general)    │   │     │ │
│  │  └─────────────┬───────────────────────────────┘   │     │ │
│  └────────────────┼───────────────────────────────────┘     │ │
│                   │                                         │ │
│        ┌──────────┴──────────┐                              │ │
│        │                     │                              │ │
│        ▼                     ▼                              │ │
│  ┌───────────────┐    ┌────────────────────────┐            │ │
│  │ LFA Module    │    │  General RAG Module    │            │ │
│  │ (Rule-Based)  │    │  (Document Retrieval)  │            │ │
│  └───────┬───────┘    └───────┬────────────────┘            │ │
│          │                    │                             │ │
│          │                    │                             │ │
│  ┌───────▼────────┐   ┌───────▼────────────────────┐        │ │
│  │  Processor     │   │  Hybrid Retriever          │        │ │
│  │  - Load CSV    │   │  ┌──────────────────────┐  │        │ │
│  │  - Check rules │   │  │ Semantic Search      │  │        │ │
│  │  - Calculate   │   │  │ (ChromaDB + Embed)   │  │        │ │
│  └───────┬────────┘   │  └──────────┬───────────┘  │        │ │
│          │            │  ┌──────────▼───────────┐  │        │ │
│          │            │  │ BM25 Fallback        │  │        │ │
│  ┌───────▼────────┐   │  │ (Keyword Matching)   │  │        │ │
│  │ Response Gen   │   │  └──────────┬───────────┘  │        │ │
│  │ (Ollama LLM)   │   │  ┌──────────▼───────────┐  │        │ │
│  └────────────────┘   │  │ RRF Fusion           │  │        │ │
│                       │  │ (Reciprocal Ranking) │  │        │ │
│                       │  └──────────────────────┘  │        │ │
│                       └───────┬────────────────────┘        │ │
│                               │                             │ │
│                        ┌──────▼─────────────────────┐       │ │
│                        │  Generator (Ollama LLM)    │       │ │
│                        │  - Build RAG prompt        │       │ │
│                        │  - Generate answer         │       │ │
│                        └────────────────────────────┘       │ │
└───────────────────────────────────────────────────────────────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  Redis Cache    │  │  ChromaDB        │  │  Ollama LLM     │
│  - Customer data│  │  - Vector DB     │  │  - llama3.2:3b  │
│  - Query results│  │  - Embeddings    │  │  - Local        │
└─────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## 3. Component Design

### 3.1 Frontend Components

#### **ChatInterface** (`ChatInterface.jsx`)
- **Purpose**: Main orchestrator for chat functionality
- **Responsibilities**:
  - Manage message state
  - Handle API communication
  - Auto-scroll to latest message
- **State**: `messages[]`, `isLoading`

#### **MessageList** (`MessageList.jsx`)
- **Purpose**: Display conversation history
- **Responsibilities**:
  - Render user and agent messages
  - Show loading indicator
  - Display empty state with example queries
- **Props**: `messages`, `isLoading`, `onExampleClick`

#### **InputBox** (`InputBox.jsx`)
- **Purpose**: Query input with tag suggestions
- **Responsibilities**:
  - Detect `@department` tags
  - Show autocomplete suggestions
  - Handle form submission
- **Features**: Tag autocomplete, keyboard shortcuts (Enter to send)

---

### 3.2 Backend Core Components

#### **Query Router** (`core/router.py`)

```python
class QueryRouter:
    """
    Routes queries to appropriate modules based on:
    - Department tag extraction (@retail_digital)
    - Customer ID extraction (regex: \d{6,})
    - Semantic intent classification (customer_specific vs general)
    """
    
    def classify_query(query: str) -> Dict:
        # 1. Extract department tag
        # 2. Extract customer ID
        # 3. Classify intent using semantic similarity
        # 4. Return routing decision
```

**Intent Classification**:
- Uses sentence embeddings (MiniLM-L6-v2)
- Compares query against intent prototypes
- Falls back to "general" if similarity < 0.5

#### **Cache Manager** (`core/cache.py`)

```python
class Cache:
    """Redis-based caching with TTL"""
    
    def get(key: str) -> Optional[Any]
    def set(key: str, value: Any, ttl: int)
    def delete(key: str)
    def health_check() -> bool
```

**Caching Strategy**:
- Customer data: 24 hours (86400s)
- Query results: 30 minutes (1800s)
- Embedding cache: 1 hour (3600s)

#### **Vector Manager** (`core/vector_manager.py`)

```python
class VectorManager:
    """
    Manages ChromaDB vector database
    - Stores document embeddings
    - Performs semantic search
    """
    
    def ingest(chunks: List[Dict])
    def query(query_text: str, top_k: int) -> List[Dict]
    def count() -> int
```

**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Speed: ~2000 sentences/second
- Quality: Balanced for retrieval tasks

---

### 3.3 Department Modules

#### **LFA Module** (Lending For All - Customer Eligibility)

**Processor** (`lfa/processor.py`)
```python
class LFAProcessor:
    """
    Rule-based eligibility checker
    - Loads customer data from CSV
    - Applies 15 eligibility rules
    - Calculates next review date
    """
    
    def check_eligibility(customer_id: str) -> Dict:
        # 1. Load customer from CSV
        # 2. Run all checks (rules.yaml)
        # 3. Generate action items
        # 4. Calculate review date
```

**Eligibility Rules** (from `rules.yaml`):
1. **Elma_check**: Active mobile banking
2. **Joint_Check**: Single ownership
3. **Mandates_Check**: Sole signatory
4. **Classification_Check**: Internal rating ≥ A5
5. **Risk_Class_Check_DS**: CRB rating ≥ A5
6. **customer_vintage_Check**: Banking ≥ 6 months
7. **DPD_Arrears_Check_DS**: No arrears > 3 days (60-day lookback)
8. **recency_check**: Consistent turnovers
9. **Turnover_Check**: Sufficient turnover
10. **Active_Inactive_Check**: Active account
11. **Linked_Base_Check**: Positive linked accounts
12. **Scheme_Check_DS**: No loan transfers
13. **Staff_Check_DS**: Not internal staff
14. **USAID_Check_DS**: Not USAID-affiliated
15. **Affordability_Check**: EMI within income

**Response Generator** (`lfa/response.py`)
```python
class ResponseGenerator:
    """
    Generates natural language explanations
    - Uses Ollama LLM (llama3.2:3b)
    - Formats eligibility results
    - Provides actionable guidance
    """
    
    def generate(eligibility_result: Dict, query: str) -> str
```

**Prompt Engineering**:
- Composed, professional tone
- Action-oriented responses
- Clear explanations without jargon
- Fallback to templates if LLM fails

---

#### **General RAG Module** (Document Q&A)

**Ingester** (`general/ingester.py`)
```python
class DocumentIngester:
    """
    Processes documents into searchable chunks
    - Supports .pdf, .txt, .md
    - Sentence-based chunking
    - Overlapping chunks for context
    """
    
    def ingest_all()
    def _chunk_text(text: str, source: str) -> List[Dict]
```

**Chunking Strategy**:
- Chunk size: 400 characters
- Overlap: 50 characters
- Preserves sentence boundaries
- Maintains source metadata

**Retriever** (`general/retriever.py`)
```python
class HybridRetriever:
    """
    Combines semantic and keyword search
    - Primary: Vector similarity (ChromaDB)
    - Fallback: BM25 keyword matching
    - Fusion: Reciprocal Rank Fusion (RRF)
    """
    
    def retrieve(query: str) -> List[Dict]:
        # 1. Semantic search (top_k * 2)
        # 2. Filter by threshold (0.55)
        # 3. If poor results, run BM25
        # 4. Fuse results using RRF
        # 5. Return top_k
```

**RRF Formula**:
```python
score = semantic_weight / (k + rank_semantic) + bm25_weight / (k + rank_bm25)
# Where: k=60, semantic_weight=0.7, bm25_weight=0.3
```

**Generator** (`general/generator.py`)
```python
class RAGGenerator:
    """
    Generates answers from retrieved context
    - Builds RAG prompt with top 3 chunks
    - Calls Ollama LLM
    - Extracts sources and confidence
    """
    
    def generate(query: str, retrieved_chunks: List[Dict]) -> Dict
```

**Prompt Template**:
```
You are a calm and professional digital assistant for NCBA Bank.

CONTEXT:
[Source 1: faqs.md]
...

QUESTION:
{query}

GUIDELINES:
1. Use ONLY the context provided
2. Keep your tone balanced — professional, clear, and considerate
3. Write 2–5 sentences
4. If the context lacks an answer, say so
5. Do NOT invent or infer beyond the context

ANSWER:
```

---

## 4. Data Flow

### 4.1 Customer Eligibility Query Flow

```
User Input: "@retail_digital why is customer 599741 excluded?"
    ↓
1. Frontend → POST /api/ask
    ↓
2. Router extracts:
   - Tag: @retail_digital
   - Customer ID: 599741
   - Intent: customer_specific
    ↓
3. LFA Processor:
   - Check cache: eligibility:599741
   - If miss → Load from CSV
   - Run 15 eligibility rules
   - Cache result (30 min TTL)
    ↓
4. Response Generator:
   - Build prompt with eligibility data
   - Call Ollama LLM
   - Clean response
   - Format with line breaks
    ↓
5. API Response:
   {
     "answer": "Hello,\n\nThe customer...",
     "metadata": {
       "customer_id": "599741",
       "overall_status": "Exclude",
       "failed_checks": [...],
       "next_review_date": "2026-01-08"
     }
   }
    ↓
6. Frontend displays formatted message
```

### 4.2 General Query Flow

```
User Input: "@retail_digital what are the eligibility requirements?"
    ↓
1. Frontend → POST /api/ask
    ↓
2. Router classifies:
   - Tag: @retail_digital
   - Customer ID: None
   - Intent: general (via semantic similarity)
    ↓
3. Hybrid Retriever:
   - Encode query → embedding vector (384-dim)
   - Search ChromaDB (top_k=10, threshold=0.55)
   - Results: 5 chunks with scores [0.78, 0.72, 0.68, 0.61, 0.59]
   - If avg_score < 0.55 → Run BM25 fallback
   - Fuse results using RRF
   - Return top 5 chunks
    ↓
4. RAG Generator:
   - Select top 3 chunks
   - Build RAG prompt with context
   - Call Ollama LLM (temp=0.4, max_tokens=512)
   - Extract sources from chunk metadata
    ↓
5. API Response:
   {
     "answer": "To qualify for an LFA loan...",
     "metadata": {
       "sources": ["faqs.md", "policies.md"],
       "confidence": "high",
       "num_chunks": 5
     }
   }
    ↓
6. Frontend displays answer
```

---

## 5. Technology Stack

### 5.1 Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI framework |
| Vite | 5.0.8 | Build tool & dev server |
| Vanilla CSS | - | Styling (no frameworks) |

### 5.2 Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.104.1 | REST API framework |
| Uvicorn | 0.24.0 | ASGI server |
| Pydantic | 2.5.0 | Data validation |
| Redis | 5.0.1 | Caching layer |

### 5.3 AI/ML Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Ollama | Latest | LLM inference engine |
| Llama 3.2 | 3B | Language model |
| ChromaDB | 0.4.22 | Vector database |
| SentenceTransformers | 2.3.1 | Text embeddings |
| Rank-BM25 | 0.2.2 | Keyword search |

### 5.4 Data Processing
| Technology | Version | Purpose |
|------------|---------|---------|
| PyPDF2 | 3.0.1 | PDF extraction |
| PyYAML | 6.0.1 | Config management |
| Pandas | 2.1.3 | CSV processing |

---

## 6. Design Patterns

### 6.1 Singleton Pattern
**Where**: Module-level instances
```python
# Example: core/cache.py
cache = Cache()  # Single instance shared across app

# Example: departments/retail_digital/modules/lfa/processor.py
processor = LFAProcessor()  # Single instance
```

**Why**: Ensures single database connection, shared cache, consistent state

### 6.2 Strategy Pattern
**Where**: Query routing and processing
```python
# Router selects strategy based on query type
if query_info['type'] == 'customer_specific':
    strategy = LFAProcessor
elif query_info['type'] == 'general':
    strategy = RAGGenerator
```

**Why**: Different processing strategies for different query types

### 6.3 Adapter Pattern
**Where**: LLM integration
```python
class ResponseGenerator:
    def _call_llm(self, prompt: str) -> str:
        # Adapts different LLM APIs to common interface
        response = requests.post(self.ollama_url, json=payload)
        return response.json().get('response', '')
```

**Why**: Abstraction allows swapping LLM providers without changing code

### 6.4 Builder Pattern
**Where**: Prompt construction
```python
def build_rag_prompt(query: str, chunks: List[Dict]) -> str:
    context = "\n\n".join(format_chunk(c) for c in chunks)
    return f"""
    CONTEXT: {context}
    QUESTION: {query}
    ANSWER:
    """
```

**Why**: Complex prompt assembly with consistent structure

### 6.5 Repository Pattern
**Where**: Data access layers
```python
class DataLoader:
    """Abstracts CSV data access"""
    def load_customer(self, customer_id: str) -> Optional[Dict]

class VectorManager:
    """Abstracts vector database operations"""
    def query(self, query_text: str) -> List[Dict]
```

**Why**: Separates business logic from data access, enables testing

---

## 7. Security & Scalability

### 7.1 Security Considerations

#### **Input Validation**
- Customer ID regex: `\d{6,}` (prevents SQL injection)
- Query length limits enforced by Pydantic
- No direct database queries from user input

#### **API Security**
- CORS configuration (currently `allow_origins=["*"]` for dev)
- Rate limiting not implemented (add in production)
- No authentication (add OAuth2/JWT for production)

#### **Data Privacy**
- Customer data cached with TTL (auto-expiry)
- No PII logged
- Redis password protection recommended

#### **LLM Safety**
- Prompt injection mitigation via system prompts
- Response cleaning removes artifacts
- Fallback templates if LLM fails

### 7.2 Scalability

#### **Horizontal Scaling**
```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ API 1 │ │ API 2 │  ← Multiple FastAPI instances
└───┬───┘ └──┬────┘
    │        │
    └────┬───┘
         │
    ┌────▼──────┐
    │  Redis    │  ← Shared cache
    │  Cluster  │
    └───────────┘
```

**Current Bottlenecks**:
1. **LLM Inference**: Ollama runs on single CPU/GPU
   - Solution: Deploy multiple Ollama instances with load balancing
2. **Vector Search**: ChromaDB is embedded
   - Solution: Use hosted ChromaDB or Pinecone
3. **CSV Data**: File-based storage
   - Solution: Migrate to PostgreSQL/MySQL

#### **Performance Optimizations**
- **Caching**: Reduces database hits by 70-80%
- **Batch Embeddings**: Process multiple queries in parallel
- **Connection Pooling**: Redis and DB connections reused
- **Lazy Loading**: Embedder loaded on first use

#### **Monitoring**
```
- Prometheus metrics (request latency, cache hit rate)
- Logging (structured JSON logs with trace IDs)
- Health checks (/health endpoint already implemented)
- Error tracking (Sentry integration)
```

---

## 8. API Reference

### 8.1 Endpoints

#### **POST /api/ask**
Query the assistant

**Request:**
```json
{
  "query": "@retail_digital check eligibility for 599741",
  "user_id": "agent_123"  // optional
}
```

**Response:**
```json
{
  "answer": "Hello,\n\nThe customer MICHAEL KYALO...",
  "metadata": {
    "customer_id": "599741",
    "overall_status": "Exclude",
    "failed_checks": [...],
    "next_review_date": "2026-01-08",
    "actions": [...]
  },
  "query_info": {
    "department": "retail_digital",
    "type": "customer_specific",
    "customer_id": "599741"
  }
}
```

#### **GET /health**
System health check

**Response:**
```json
{
  "status": "healthy",  // or "degraded"
  "redis": true,
  "ollama": true
}
```

#### **POST /api/ingest**
Trigger document re-ingestion

**Response:**
```json
{
  "status": "success",
  "message": "Ingested documents successfully. Total chunks: 145"
}
```

---

## 9. Configuration Files

### 9.1 rules.yaml (LFA Module)
Defines eligibility rules with:
- Rule name and description
- CSV column mapping
- Required values
- Exclusion reasons
- Policy parameters (cooling periods, thresholds)

### 9.2 module.yaml (General Module)
Configures RAG behavior:
- Chunk size and overlap
- Top-k retrieval count
- Similarity threshold
- Retrieval weights (semantic vs BM25)
- Generation parameters (max tokens, temperature)

### 9.3 .env (Environment)
Runtime configuration:
- Redis connection URL
- Ollama host and model
- Cache TTLs
- API host and port

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation - combines document retrieval with LLM generation |
| **LFA** | Lending For All - NCBA's digital loan product |
| **BM25** | Best Match 25 - statistical ranking function for keyword search |
| **RRF** | Reciprocal Rank Fusion - method for combining multiple ranked lists |
| **DPD** | Days Past Due - measure of loan arrears |
| **CRB** | Credit Reference Bureau - credit scoring agency |
| **TTL** | Time To Live - cache expiration time |
| **Embedding** | Vector representation of text for semantic search |

---

## Conclusion

The NCBA Personal Assistant demonstrates a hybrid approach to conversational AI:
- **Rule-based processing** for structured eligibility checks
- **RAG architecture** for flexible document-based Q&A
- **Modular design** for easy extension to new departments/products
- **Local LLM deployment** for data privacy and cost efficiency

The system balances accuracy, speed, and maintainability while remaining extensible for future banking products and use cases.