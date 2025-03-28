from typing import Optional, Any, Callable
from datetime import datetime, time
from functools import lru_cache
from threading import Lock

class InMemoryCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl_seconds
        self.lock = Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key not in self.cache:
                return None
            
            timestamp = self.timestamps.get(key)
            if not timestamp:
                return None
                
            # Check if expired
            now = datetime.now().timestamp()
            if now - timestamp > self.ttl:
                # Clean up expired entry
                del self.cache[key]
                del self.timestamps[key]
                return None
                
            return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with timestamp."""
        with self.lock:
            self.cache[key] = value
            self.timestamps[key] = datetime.now().timestamp()
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()

class CacheManager:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        """Initialize cache manager with max size and TTL in seconds."""
        self.cache = InMemoryCache(ttl_seconds=ttl)
        self.max_size = max_size
        
    @lru_cache(maxsize=100)
    def memoize(self, func: Callable, *args, **kwargs) -> Any:
        """Memoize function results."""
        return func(*args, **kwargs)
    
    def get_or_set(self, key: str, getter_func: Callable) -> Any:
        """Get from cache or set if not exists."""
        value = self.cache.get(key)
        if value is not None:
            return value
            
        value = getter_func()
        if value is not None:
            self.cache.set(key, value)
        return value
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        self.memoize.cache_clear() 