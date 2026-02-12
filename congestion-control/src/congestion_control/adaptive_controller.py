from __future__ import annotations

import time
from dataclasses import dataclass

from .token_bucket import TokenBucket


@dataclass
class AdaptiveCongestionController:
    """
    Adapts the rate of a TokenBucket based on congestion feedback.
    Uses an additive increase, multiplicative decrease (AIMD) strategy by default.
    """
    bucket: TokenBucket
    increase_factor: float = 1.1
    decrease_factor: float = 0.7
    min_rate: float = 1.0
    max_rate: float = 1000.0
    high_latency_threshold: float = 500.0  # ms
    _last_feedback: float | None = None

    def on_success(self, rtt_ms: float | None = None) -> None:
        """
        Signal a successful operation.
        If rtt_ms is provided and is below high_latency_threshold, increase rate.
        If rtt_ms is high, do not increase (hold steady).
        """
        if rtt_ms is not None and rtt_ms > self.high_latency_threshold:
            return  # high latency; hold steady
        
        self.bucket.rate = min(self.max_rate, self.bucket.rate * self.increase_factor)
        self._last_feedback = time.monotonic()

    def on_congestion_signal(self) -> None:
        """
        Signal that congestion (packet loss, error) occurred.
        Reduces the rate immediately.
        """
        self.bucket.rate = max(self.min_rate, self.bucket.rate * self.decrease_factor)
        self._last_feedback = time.monotonic()

    def allow(self, cost: float = 1.0) -> bool:
        """Delegate to the underlying token bucket."""
        return self.bucket.allow(cost)
