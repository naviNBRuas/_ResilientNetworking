from __future__ import annotations

import json
import os
import tempfile
from abc import ABC, abstractmethod
from typing import Dict
import logging

from .models import Operation

logger = logging.getLogger(__name__)


class OperationStore(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Operation]:
        ...

    @abstractmethod
    def save(self, operations: Dict[str, Operation]) -> None:
        ...


class InMemoryOperationStore(OperationStore):
    def __init__(self):
        self._ops: Dict[str, Operation] = {}

    def load(self) -> Dict[str, Operation]:
        return dict(self._ops)

    def save(self, operations: Dict[str, Operation]) -> None:
        self._ops = dict(operations)


class FileOperationStore(OperationStore):
    def __init__(self, path: str):
        self.path = path

    def load(self) -> Dict[str, Operation]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: Operation.from_dict(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load operations from {self.path}: {e}")
            # Decision: Return empty or raise? For resilience, maybe backup bad file and start fresh?
            # For now, let's log and re-raise to alert the user/caller, as data loss is critical.
            raise

    def save(self, operations: Dict[str, Operation]) -> None:
        serializable = {k: v.to_dict() for k, v in operations.items()}
        dir_name = os.path.dirname(self.path) or "."
        
        # Create temp file in the same directory to ensure atomic move works
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replacement
            os.replace(tmp_path, self.path)
        except OSError as e:
            logger.error(f"Failed to save operations to {self.path}: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
