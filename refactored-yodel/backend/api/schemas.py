from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    """Request model for /api/ask endpoint"""
    query: str
    user_id: Optional[str] = "agent_default"

class QueryResponse(BaseModel):
    """
    Response model for /api/ask endpoint
    
    Metadata contains different fields based on query type:
    - Customer-specific: eligibility data, failed_checks, next_review_date, etc.
    - General RAG: sources, confidence, num_chunks
    """
    answer: str
    metadata: Dict[str, Any]
    query_info: Dict[str, Any]

class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str
    redis: bool
    ollama: bool

class IngestResponse(BaseModel):
    """Response model for /api/ingest endpoint"""
    status: str
    message: str
    total_chunks: Optional[int] = 0