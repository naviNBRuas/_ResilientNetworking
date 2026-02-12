from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExponentialBackoff:
    base: float = 0.05
    factor: float = 2.0
    max_delay: float = 5.0
    jitter: float = 0.2  # proportion of delay to jitter by +/- jitter*delay

    def compute(self, attempt: int) -> float:
        delay = min(self.base * (self.factor ** (attempt - 1)), self.max_delay)
        if self.jitter > 0:
            spread = delay * self.jitter
            delay = random.uniform(delay - spread, delay + spread)
        return max(0.0, delay)
