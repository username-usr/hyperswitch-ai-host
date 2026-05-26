import redis
import json
import hashlib
from config.settings import settings

class DiagnosticCacheManager:
    def __init__(self):
    # Forced explicit IPv4 routing to match the Docker engine host bridge
        self.client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
        
    def _generate_log_hash(self, error_log: str) -> str:
        """Converts raw unformatted logs into a deterministic, fixed-length unique signature key."""
        return hashlib.sha256(error_log.strip().encode('utf-8')).hexdigest()

    def get_cached_analysis(self, error_log: str) -> str | None:
        """Attempts to extract an existing diagnostic string from Redis memory."""
        try:
            cache_key = f"diag:{self._generate_log_hash(error_log)}"
            return self.client.get(cache_key)
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            # 💡 FIXED: Correct lowercase module path for Redis exceptions
            print("WARNING: Redis Cache unreachable. Defaulting to live model pass.")
            return None

    def set_cached_analysis(self, error_log: str, analysis_text: str, ttl_seconds: int = 3600):
        """Stores a freshly generated solution matrix inside Redis with an expiration safeguard."""
        try:
            cache_key = f"diag:{self._generate_log_hash(error_log)}"
            self.client.setex(cache_key, settings.REDIS_TTL, analysis_text)
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            # 💡 FIXED: Correct lowercase module path for Redis exceptions
            pass

# Singleton accessor instance
cache_manager = None

def get_cache_manager():
    global cache_manager
    if cache_manager is None:
        cache_manager = DiagnosticCacheManager()
    return cache_manager