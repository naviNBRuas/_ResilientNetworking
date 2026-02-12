from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 5.0
    half_open_max_calls: int = 1
    success_threshold: int = 1
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _successes: int = field(default=0, init=False)
    _opened_at: float | None = field(default=None, init=False)
    _half_open_attempts: int = field(default=0, init=False)

    def allow_request(self) -> bool:
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            if self._opened_at is None:
                return False
            if time.time() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempts = 0
                self._successes = 0
                return True
            return False
        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_attempts < self.half_open_max_calls:
                self._half_open_attempts += 1
                return True
            return False
        return False

    def record_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._successes += 1
            if self._successes >= self.success_threshold:
                self._reset()
        else:
            self._reset()

    def record_failure(self) -> None:
        self._failures += 1
        if self._state == CircuitState.HALF_OPEN or self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
            self._successes = 0

    def _reset(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None
        self._half_open_attempts = 0
        self._successes = 0

    @property
    def state(self) -> CircuitState:
        return self._state
