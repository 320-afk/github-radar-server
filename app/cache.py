"""In-memory LRU cache for GitHub API responses."""

import time
from typing import Any, Optional

from cachetools import TTLCache


class GitHubCache:
    """Thread-safe in-memory cache with TTL for GitHub API responses."""

    def __init__(self, maxsize: int = 500, ttl_seconds: int = 300):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._timestamps: dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired."""
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Store value in cache with current timestamp."""
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def get_with_age(self, key: str) -> tuple[Optional[Any], Optional[float]]:
        """Return (value, age_seconds) or (None, None) if not cached."""
        value = self._cache.get(key)
        if value is None:
            return None, None
        age = time.time() - self._timestamps.get(key, 0)
        return value, age

    def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._timestamps.clear()

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)


# Global cache instance - shared across requests
github_cache = GitHubCache(maxsize=500, ttl_seconds=300)

# Global repository cache to track known repositories by repo_id
repo_cache: dict[str, Any] = {}
