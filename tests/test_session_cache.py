import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.storage.cache import InMemoryCache


def test_in_memory_cache_get_set_delete():
    cache = InMemoryCache()
    cache.set("key1", {"a": 1})
    assert cache.get("key1") == {"a": 1}
    cache.delete("key1")
    assert cache.get("key1") is None


def test_in_memory_cache_clear():
    cache = InMemoryCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_in_memory_cache_not_shared_across_instances():
    cache_a = InMemoryCache()
    cache_b = InMemoryCache()
    cache_a.set("shared", "value")
    assert cache_b.get("shared") is None
