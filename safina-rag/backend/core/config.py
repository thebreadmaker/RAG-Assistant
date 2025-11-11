from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # ============ CHANGED: Added LLM Provider Selection ============
    # LLM Provider: "ollama" or "poe"
    llm_provider: str = "ollama"
    # ================================================================
    
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "tinyllama"
    
    # ============ CHANGED: Added Poe Configuration ============
    # Poe Configuration
    poe_api_key: str = ""
    poe_model: str = "Claude-Opus-4.1"
    # ===========================================================
    
    # Cache TTLs
    customer_cache_ttl: int = 86400
    query_cache_ttl: int = 1800
    embedding_cache_ttl: int = 3600
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # RAG Settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_db_persist_dir: Path = Path(__file__).parent.parent / "departments"
    chunk_size: int = 400
    chunk_overlap: int = 50
    top_k: int = 5
    similarity_threshold: float = 0.55
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()