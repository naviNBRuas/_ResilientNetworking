from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Container for a cached value and its creation timestamp."""
    value: Any
    timestamp: float


class IdempotencyCache:
    """
    A thread-safe, in-memory cache for idempotency keys with TTL support.
    
    Attributes:
        ttl (float): Time-to-live for cache entries in seconds.
    """

    def __init__(self, ttl_seconds: float = 600):
        """
        Initialize the IdempotencyCache.

        Args:
            ttl_seconds (float): Time-to-live for cache entries in seconds. Defaults to 600.
        """
        self.ttl = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def remember(self, key: str, value: Any) -> Any:
        """
        Store a value in the cache. Overwrites existing keys.

        Args:
            key (str): The idempotency key.
            value (Any): The value to store.

        Returns:
            Any: The stored value.
        """
        with self._lock:
            self._cache[key] = CacheEntry(value=value, timestamp=time.time())
            logger.debug("Remembered key: %s", key)
            return value

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache if it exists and hasn't expired.

        Args:
            key (str): The idempotency key.

        Returns:
            Optional[Any]: The cached value, or None if not found or expired.
        """
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            
            if time.time() - entry.timestamp > self.ttl:
                del self._cache[key]
                logger.debug("Key expired during get: %s", key)
                return None
            
            return entry.value

    def cleanup(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            int: The number of entries removed.
        """
        now = time.time()
        with self._lock:
            expired = [k for k, v in self._cache.items() if now - v.timestamp > self.ttl]
            for k in expired:
                del self._cache[k]
            
            if expired:
                logger.info("Cleaned up %d expired keys", len(expired))
            return len(expired)
