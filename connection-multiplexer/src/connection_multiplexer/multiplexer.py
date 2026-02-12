from __future__ import annotations

import logging
import random
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .errors import MultiplexingError, TransportError
from .transports import Transport

logger = logging.getLogger(__name__)


@dataclass(order=True)
class TransportRegistryEntry:
    priority: int
    name: str
    transport: Transport
    selection_weight: float = 1.0


class ConnectionMultiplexer:
    """Resilient multiplexer that routes payloads across multiple transports."""

    def __init__(self, on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """
        Args:
            on_event: Optional callback(event_name, details) for observability.
        """
        self._registry: List[TransportRegistryEntry] = []
        self._lock = threading.Lock()
        self._on_event = on_event

    def _emit(self, event: str, **kwargs: Any) -> None:
        if self._on_event:
            try:
                self._on_event(event, kwargs)
            except Exception:
                # Observer code should not break the multiplexer
                logger.exception("Error in observability callback")

    def register(self, name: str, transport: Transport, *, priority: int = 100, weight: float = 1.0) -> None:
        """Register a transport with the multiplexer.
        
        Args:
            name: Unique identifier for the transport
            transport: Transport instance to register
            priority: Lower values = higher priority (default 100)
            weight: Selection weight within priority tier (default 1.0)
            
        Raises:
            ValueError: If name is empty or weight is invalid
            RuntimeError: If transport fails to connect
        """
        if not name or not name.strip():
            raise ValueError("Transport name must not be empty")
        if weight <= 0:
            raise ValueError(f"Transport weight must be positive, got {weight}")
        
        try:
            transport.connect()
        except Exception as e:
            logger.error(f"Failed to connect transport '{name}': {e}")
            raise RuntimeError(f"Transport connection failed for '{name}'") from e
        
        entry = TransportRegistryEntry(priority=priority, name=name, transport=transport, selection_weight=weight)
        with self._lock:
            # Prevent duplicate registration
            if any(e.name == name for e in self._registry):
                logger.warning(f"Transport '{name}' already registered, replacing")
                self._registry = [e for e in self._registry if e.name != name]
            self._registry.append(entry)
            self._registry.sort()  # priority ascending
        logger.info(f"Registered transport '{name}' (priority={priority}, weight={weight})")

    def unregister(self, name: str) -> None:
        with self._lock:
            self._registry = [e for e in self._registry if e.name != name]

    def _select_candidates(self) -> List[TransportRegistryEntry]:
        with self._lock:
            return list(self._registry)

    def send(self, payload: Any, *, predicate: Optional[Callable[[Transport], bool]] = None) -> Dict[str, Any]:
        """Send payload through the best available transport.
        
        Selects transports by priority, then weighted health/preference within tier.
        Tries each transport in order until one succeeds.
        
        Args:
            payload: Data to send (any serializable type)
            predicate: Optional filter function to exclude transports
            
        Returns:
            Dict with keys: result (response), via (transport name), attempted (list of tried transports)
            
        Raises:
            MultiplexingError: If all transports fail or none are available
            ValueError: If payload is None
        """
        if payload is None:
            raise ValueError("Payload cannot be None")
        
        attempted: List[str] = []
        last_error: Optional[Exception] = None
        candidates = self._select_candidates()

        if not candidates:
            raise MultiplexingError("No transports registered", attempted=[])

        # Group by priority to allow weighted choice within priority tier
        priority_groups: Dict[int, List[TransportRegistryEntry]] = {}
        for entry in candidates:
            if predicate and not predicate(entry.transport):
                continue
            priority_groups.setdefault(entry.priority, []).append(entry)

        for priority in sorted(priority_groups.keys()):
            tier = priority_groups[priority]
            if not tier:
                continue

            weights = [max(0.0001, e.selection_weight * e.transport.health()) for e in tier]
            # sample without replacement using weights
            sampled_indices: List[int] = []
            local_tier = tier.copy()
            local_weights = weights.copy()
            while local_tier:
                choice = random.choices(range(len(local_tier)), weights=local_weights, k=1)[0]
                sampled_indices.append(choice)
                local_tier.pop(choice)
                local_weights.pop(choice)

            for idx in sampled_indices:
                entry = tier[idx]
                attempted.append(entry.name)
                try:
                    logger.debug(f"Attempting send via '{entry.name}'")
                    self._emit("send_attempt", transport=entry.name, payload=payload)
                    result = entry.transport.send(payload)
                    logger.info(f"Send succeeded via '{entry.name}' after {len(attempted)} attempt(s)")
                    self._emit("send_success", transport=entry.name, attempts=len(attempted))
                    return {
                        "result": result,
                        "via": entry.name,
                        "attempted": attempted,
                    }
                except TransportError as e:
                    last_error = e
                    logger.debug(f"Transport '{entry.name}' failed: {e}")
                    self._emit("transport_failure", transport=entry.name, error=str(e))
                    continue

        logger.error(f"All {len(attempted)} transports exhausted")
        self._emit("multiplex_failure", attempted=attempted, error=str(last_error))
        raise MultiplexingError(
            f"No healthy transport succeeded (tried {len(attempted)})",
            attempted=attempted,
            last_error=last_error
        )

    def heartbeat(self) -> Dict[str, float]:
        """Return health scores for transports."""
        with self._lock:
            return {entry.name: entry.transport.health() for entry in self._registry}

    def close(self) -> None:
        with self._lock:
            for entry in self._registry:
                entry.transport.close()
            self._registry.clear()
