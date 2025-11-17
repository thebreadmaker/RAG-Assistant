import redis
import json
from typing import Optional, Any
from core.config import get_settings
from core.logger import logger

settings = get_settings()

class Cache:
    def __init__(self):
        logger.info("🔄 Initializing Cache client...")
        try:
            self.client = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info(f"✅ Cache client initialized - Redis URL: {settings.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cache client: {str(e)}", exc_info=True)
            raise
    
    def get(self, key: str) -> Optional[Any]:
        logger.debug(f"💾 Cache GET: {key}")
        try:
            data = self.client.get(key)
            if data:
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(data)
            else:
                logger.debug(f"⚠️ Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"❌ Cache get error for key {key}: {str(e)}", exc_info=True)
            return None
    
    def set(self, key: str, value: Any, ttl: int):
        logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
        try:
            self.client.setex(key, ttl, json.dumps(value))
            logger.debug(f"✅ Cache SET successful: {key}")
        except Exception as e:
            logger.error(f"❌ Cache set error for key {key}: {str(e)}", exc_info=True)
    
    def delete(self, key: str):
        logger.debug(f"💾 Cache DELETE: {key}")
        try:
            result = self.client.delete(key)
            logger.debug(f"✅ Cache DELETE successful: {key} (deleted: {result})")
        except Exception as e:
            logger.error(f"❌ Cache delete error for key {key}: {str(e)}", exc_info=True)
    
    def health_check(self) -> bool:
        logger.debug("🏥 Cache health check...")
        try:
            result = self.client.ping()
            logger.debug(f"✅ Cache health check OK")
            return result
        except Exception as e:
            logger.error(f"❌ Cache health check failed: {str(e)}", exc_info=True)
            return False

cache = Cache()