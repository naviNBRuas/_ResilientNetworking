from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Deduplicator:
    """
    A thread-safe, TTL-based deduplicator.
    
    Tracks keys and their timestamps. Keys older than `ttl_seconds` are considered expired
    and effectively "unseen". Enforces a maximum capacity to prevent memory leaks.
    """
    ttl_seconds: float = 300.0
    max_count: int = 10000
    
    _seen: Dict[str, float] = field(default_factory=dict, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self):
        pass

    def seen(self, key: str) -> bool:
        """
        Check if a key has been seen recently.
        
        Returns:
            True if the key was seen within the last `ttl_seconds`.
            False if the key is new or expired.
        """
        now = time.time()
        with self._lock:
            ts = self._seen.get(key)
            
            # If key exists, check expiry
            if ts is not None:
                if now - ts <= self.ttl_seconds:
                    # Seen and valid. Move to end (LRU behavior) and update timestamp.
                    del self._seen[key]
                    self._seen[key] = now
                    return True
                else:
                    # Expired, treat as new
                    pass

            # Not seen or expired
            self._seen[key] = now
            
            # Check capacity
            if len(self._seen) > self.max_count:
                self._cleanup_locked(now)
                # If still too big, force remove oldest (first inserted/updated)
                while len(self._seen) > self.max_count:
                    # Remove the first item (FIFO/LRU)
                    first_key = next(iter(self._seen))
                    del self._seen[first_key]
            
            return False

    def cleanup(self) -> int:
        """
        Manually trigger cleanup of expired keys.
        """
        with self._lock:
            return self._cleanup_locked(time.time())

    def _cleanup_locked(self, now: float) -> int:
        expired = [k for k, ts in self._seen.items() if now - ts > self.ttl_seconds]
        for k in expired:
            del self._seen[k]
        return len(expired)
