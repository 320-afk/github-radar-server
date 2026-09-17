"""Unit tests for the GitHub cache module."""

import time
import pytest

from app.cache import GitHubCache


class TestGitHubCache:
    def test_set_and_get(self):
        cache = GitHubCache(maxsize=10, ttl_seconds=60)
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_missing_key(self):
        cache = GitHubCache()
        assert cache.get("nonexistent") is None

    def test_get_with_age(self):
        cache = GitHubCache(ttl_seconds=60)
        cache.set("key1", "value")
        value, age = cache.get_with_age("key1")
        assert value == "value"
        assert age >= 0

    def test_invalidate(self):
        cache = GitHubCache()
        cache.set("key1", "value")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = GitHubCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.size == 0

    def test_size_property(self):
        cache = GitHubCache()
        assert cache.size == 0
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        assert cache.size == 2

    def test_lru_eviction(self):
        """When maxsize is reached, oldest entries should be evicted."""
        cache = GitHubCache(maxsize=3, ttl_seconds=60)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")
        cache.set("k4", "v4")  # Should evict k1
        assert cache.get("k1") is None
        assert cache.get("k4") == "v4"

    def test_ttl_expiry(self):
        """Entry should expire after TTL."""
        cache = GitHubCache(maxsize=10, ttl_seconds=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.5)
        assert cache.get("key1") is None
