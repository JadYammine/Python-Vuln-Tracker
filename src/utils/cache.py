import time, hashlib, inspect

def ttl_cache(seconds: int = 3600):
    """
    Works for sync or async callables.
    Key is SHA-256 of args/kwargs repr → (insert_time, result).
    """
    def decorator(fn):
        cache = {}

        async def _async_wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            now = time.time()
            if key in cache and now - cache[key][0] < seconds:
                return cache[key][1]
            result = await fn(*args, **kwargs)
            cache[key] = (now, result)
            return result

        def _sync_wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            now = time.time()
            if key in cache and now - cache[key][0] < seconds:
                return cache[key][1]
            result = fn(*args, **kwargs)
            cache[key] = (now, result)
            return result

        def _make_key(a, k):
            return hashlib.sha256(repr((a, k)).encode()).hexdigest()

        return _async_wrapper if inspect.iscoroutinefunction(fn) else _sync_wrapper
    return decorator
