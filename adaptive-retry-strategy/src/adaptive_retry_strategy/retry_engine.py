from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple

from .circuit_breaker import CircuitBreaker
from .policy import RetryPolicy


@dataclass
class RetryOutcome:
    attempts: int
    result: Any = None
    error: Optional[BaseException] = None
    duration: float = 0.0

    @property
    def succeeded(self) -> bool:
        return self.error is None


class RetryEngine:
    def __init__(self, policy: RetryPolicy, *, circuit_breaker: CircuitBreaker | None = None):
        self.policy = policy
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> RetryOutcome:
        start = time.time()
        attempts = 0
        last_err: BaseException | None = None
        for delay in self.policy.delays():
            if not self.circuit_breaker.allow_request():
                return RetryOutcome(attempts=attempts, error=RuntimeError("circuit-open"), duration=time.time() - start)

            attempts += 1
            try:
                result = func(*args, **kwargs)
                self.circuit_breaker.record_success()
                return RetryOutcome(attempts=attempts, result=result, duration=time.time() - start)
            except Exception as exc:  # catch Exception to avoid holding KeyboardInterrupt/SystemExit
                last_err = exc
                if not self.policy.should_retry(exc):
                    self.circuit_breaker.record_failure()
                    raise
                self.circuit_breaker.record_failure()
                if attempts < self.policy.max_attempts:
                    time.sleep(delay)

        return RetryOutcome(attempts=attempts, error=last_err, duration=time.time() - start)
