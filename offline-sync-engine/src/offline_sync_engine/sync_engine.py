from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List

from .models import Operation
from .resolver import ConflictResolver, LastWriteWinsResolver
from .store import OperationStore

logger = logging.getLogger(__name__)


@dataclass
class SyncEngine:
    store: OperationStore
    resolver: ConflictResolver = field(default_factory=LastWriteWinsResolver)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self):
        self._lock = threading.RLock()
        try:
            self._operations: Dict[str, Operation] = self.store.load()
            logger.info(f"Loaded {len(self._operations)} operations from store.")
        except Exception as e:
            logger.error(f"Failed to initialize SyncEngine: {e}")
            raise

    @property
    def state(self) -> Dict[str, Operation]:
        with self._lock:
            return dict(self._operations)

    def enqueue(self, key: str, value: object, *, author: str, version: int | None = None) -> Operation:
        with self._lock:
            current = self._operations.get(key)
            next_version = (current.version + 1) if current and version is None else (version or 1)
            op = Operation(key=key, value=value, version=next_version, author=author)
            resolved = self.resolver.resolve(current, op)
            
            logger.debug(f"Enqueued operation: {resolved.key} v{resolved.version}")

            self._operations[key] = resolved
            try:
                self.store.save(self._operations)
            except Exception as e:
                logger.error(f"Failed to persist enqueue operation for key {key}: {e}")
                raise
            
            return resolved

    def reconcile(self, incoming: Iterable[Operation]) -> List[Operation]:
        applied: List[Operation] = []
        with self._lock:
            for op in incoming:
                local = self._operations.get(op.key)
                resolved = self.resolver.resolve(local, op)
                if resolved is not local:
                    self._operations[op.key] = resolved
                    applied.append(resolved)
            
            if applied:
                try:
                    self.store.save(self._operations)
                    logger.info(f"Reconciled {len(applied)} operations.")
                except Exception as e:
                    logger.error(f"Failed to persist reconciled operations: {e}")
                    raise
        return applied

    def sync(self, pull_remote: Callable[[], Iterable[Operation]], push_remote: Callable[[Iterable[Operation]], None]) -> Dict[str, int]:
        with self._lock:
            try:
                remote_ops = list(pull_remote())
            except Exception as e:
                logger.error(f"Failed to pull remote operations: {e}")
                raise

            applied_remote = self.reconcile(remote_ops)
            
            try:
                push_remote(list(self._operations.values()))
            except Exception as e:
                logger.error(f"Failed to push remote operations: {e}")
                # We partially succeeded (pulled and applied), so we might not want to fail completely?
                # But the contract implies a full sync. Let's raise.
                raise

            return {
                "applied_remote": len(applied_remote),
                "pushed": len(self._operations),
            }
