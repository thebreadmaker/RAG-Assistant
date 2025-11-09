from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "tinyllama"
    customer_cache_ttl: int = 86400
    query_cache_ttl: int = 1800
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()