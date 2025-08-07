import time
import pytest
from src.utils.cache import ttl_cache

@ttl_cache(seconds=1)
def add(x, y):
    return x + y

@ttl_cache(seconds=1)
def slow_add(x, y):
    time.sleep(0.1)
    return x + y

def test_ttl_cache_hit_and_expiry():
    # First call, should compute
    result1 = add(1, 2)
    # Second call, should hit cache
    result2 = add(1, 2)
    assert result1 == result2
    # Wait for cache to expire
    time.sleep(1.1)
    result3 = add(1, 2)
    assert result3 == result1


def test_ttl_cache_hit_rate():
    start = time.time()
    result1 = slow_add(2, 3)
    duration1 = time.time() - start

    start = time.time()
    result2 = slow_add(2, 3)
    duration2 = time.time() - start

    assert result1 == result2 == 5
    # The second call should be much faster (cache hit)
    assert duration2 < duration1 / 2
