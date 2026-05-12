import time
from functools import wraps

_ttl_cache = {}

def cached(ttl_seconds=30):
    """Simple in-memory cache with TTL."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in _ttl_cache:
                val, timestamp = _ttl_cache[key]
                if now - timestamp < ttl_seconds:
                    return val
            result = func(*args, **kwargs)
            _ttl_cache[key] = (result, now)
            return result
        return wrapper
    return decorator

def cache_clear():
    _ttl_cache.clear()