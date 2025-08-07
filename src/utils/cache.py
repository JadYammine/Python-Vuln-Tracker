import time
import hashlib
import inspect
import asyncio
from collections import OrderedDict
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class LRUCache:
    """LRU cache with memory management and TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            timestamp, value = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.cache.move_to_end(key)
                self.hits += 1
                return value
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        
        self.cache[key] = (time.time(), value)
    
    def get_stats(self) -> dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "size": len(self.cache),
            "max_size": self.max_size
        }

def ttl_cache(seconds: int = 3600, max_size: int = 1000):
    """
    Enhanced TTL cache with LRU eviction and performance monitoring.
    Works for sync or async callables.
    """
    def decorator(fn):
        cache = LRUCache(max_size=max_size, ttl=seconds)
        
        async def _async_wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            
            result = await fn(*args, **kwargs)
            cache.set(key, result)
            return result

        def _sync_wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result

        def _make_key(a, k):
            return hashlib.sha256(repr((a, k)).encode()).hexdigest()
        
        # Add cache stats to the wrapper
        wrapper = _async_wrapper if inspect.iscoroutinefunction(fn) else _sync_wrapper
        wrapper.cache_stats = cache.get_stats
        wrapper.cache_clear = cache.cache.clear
        
        return wrapper
    return decorator
