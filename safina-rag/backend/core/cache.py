import redis
import json
from typing import Optional, Any
from core.config import get_settings

settings = get_settings()

class Cache:
    def __init__(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int):
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def health_check(self) -> bool:
        try:
            return self.client.ping()
        except:
            return False

cache = Cache()