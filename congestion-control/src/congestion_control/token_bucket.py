from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    rate: float  # tokens per second
    capacity: float
    tokens: float | None = None
    last: float | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False, init=False)

    def __post_init__(self):
        if self.rate <= 0:
            raise ValueError("Rate must be positive")
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        with self._lock:
            if self.tokens is None:
                self.tokens = self.capacity
            if self.last is None:
                self.last = time.monotonic()

    def allow(self, cost: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            last = self.last if self.last is not None else now
            elapsed = now - last
            self.last = now
            
            # Refill
            self.tokens = min(self.capacity, (self.tokens or 0) + elapsed * self.rate)
            
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False
