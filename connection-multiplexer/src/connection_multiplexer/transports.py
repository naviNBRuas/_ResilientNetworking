from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import TransportError


class Transport(ABC):
    """Abstract transport that can carry payloads and report health."""

    name: str

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def send(self, payload: Any) -> Any:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def health(self) -> float:
        """Return a health score in [0,1]; 1 means fully healthy."""
        ...

    def __enter__(self) -> "Transport":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


class LogTransport(Transport):
    """Production-ready transport that logs payloads to a logger (for testing/debug)."""
    
    def __init__(self, name: str, logger_instance: logging.Logger):
        self.name = name
        self.logger = logger_instance
        self._connected = False

    def connect(self) -> None:
        self._connected = True
        self.logger.info(f"[{self.name}] Connected")

    def send(self, payload: Any) -> Any:
        if not self._connected:
            raise TransportError(f"[{self.name}] Not connected")
        self.logger.info(f"[{self.name}] Sending: {payload}")
        return {"status": "sent", "payload_repr": repr(payload)}

    def close(self) -> None:
        self._connected = False
        self.logger.info(f"[{self.name}] Closed")

    def health(self) -> float:
        return 1.0


@dataclass
class SimulatedTransport(Transport):
    """Simple transport that simulates latency, jitter, and drop/fail behavior."""

    name: str
    base_latency_ms: float = 5.0
    jitter_ms: float = 3.0
    drop_rate: float = 0.0
    fail_after: Optional[int] = None
    _sent: int = field(default=0, init=False)
    _connected: bool = field(default=False, init=False)
    _last_error_ts: Optional[float] = field(default=None, init=False)

    def connect(self) -> None:
        self._connected = True

    def send(self, payload: Any) -> Any:
        if not self._connected:
            raise TransportError(f"Transport {self.name} is not connected")

        self._sent += 1
        if self.fail_after is not None and self._sent > self.fail_after:
            self._last_error_ts = time.time()
            raise TransportError(f"Transport {self.name} exceeded fail_after={self.fail_after}")

        if random.random() < self.drop_rate:
            self._last_error_ts = time.time()
            raise TransportError(f"Transport {self.name} dropped the payload")

        latency = self.base_latency_ms + random.random() * self.jitter_ms
        time.sleep(latency / 1000.0)
        return {
            "transport": self.name,
            "payload": payload,
            "latency_ms": latency,
            "sent_index": self._sent,
        }

    def close(self) -> None:
        self._connected = False

    def health(self) -> float:
        # Penalize recent errors
        if self._last_error_ts is None:
            return 1.0
        age = time.time() - self._last_error_ts
        if age > 10:
            return 0.9
        if age > 5:
            return 0.7
        return 0.4
