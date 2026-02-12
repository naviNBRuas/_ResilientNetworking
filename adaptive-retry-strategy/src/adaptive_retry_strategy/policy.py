from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Tuple, Type

from .backoff import ExponentialBackoff


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    retry_on: Tuple[Type[BaseException], ...] = (Exception,)
    backoff: ExponentialBackoff = field(default_factory=ExponentialBackoff)

    def should_retry(self, exc: BaseException) -> bool:
        return isinstance(exc, self.retry_on)

    def delays(self) -> Iterable[float]:
        for attempt in range(1, self.max_attempts + 1):
            yield self.backoff.compute(attempt)
