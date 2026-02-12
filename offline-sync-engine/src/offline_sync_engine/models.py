from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Operation:
    key: str
    value: Any
    version: int
    author: str
    op_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "version": self.version,
            "author": self.author,
            "op_id": self.op_id,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Operation":
        return Operation(
            key=data["key"],
            value=data["value"],
            version=int(data["version"]),
            author=data["author"],
            op_id=data.get("op_id", str(uuid.uuid4())),
            timestamp=float(data.get("timestamp", time.time())),
        )
