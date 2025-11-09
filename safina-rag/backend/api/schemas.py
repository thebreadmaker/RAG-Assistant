from pydantic import BaseModel
from typing import Optional, List, Dict

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "agent_default"

class QueryResponse(BaseModel):
    answer: str
    metadata: Dict
    query_info: Dict

class HealthResponse(BaseModel):
    status: str
    redis: bool
    ollama: bool