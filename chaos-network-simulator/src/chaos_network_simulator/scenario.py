from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional, Union, Dict, Any
from pathlib import Path


@dataclass
class Scenario:
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    drop_rate: float = 0.0
    fault_rate: float = 0.0
    throttle_rps: Optional[float] = None
    duration_limit_sec: Optional[float] = None

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.jitter_ms < 0:
            raise ValueError("jitter_ms must be non-negative")
        if not (0.0 <= self.drop_rate <= 1.0):
            raise ValueError("drop_rate must be between 0.0 and 1.0")
        if not (0.0 <= self.fault_rate <= 1.0):
            raise ValueError("fault_rate must be between 0.0 and 1.0")
        if self.throttle_rps is not None and self.throttle_rps <= 0:
            raise ValueError("throttle_rps must be positive")
        if self.duration_limit_sec is not None and self.duration_limit_sec <= 0:
            raise ValueError("duration_limit_sec must be positive")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Scenario:
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, json_str_or_path: Union[str, Path]) -> Scenario:
        if isinstance(json_str_or_path, Path) or (isinstance(json_str_or_path, str) and json_str_or_path.endswith(".json")):
            with open(json_str_or_path, 'r') as f:
                data = json.load(f)
        else:
            data = json.loads(json_str_or_path)
        return cls.from_dict(data)

    def to_json(self, path: Optional[Union[str, Path]] = None) -> str:
        data = self.to_dict()
        if path:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return ""
        return json.dumps(data, indent=2)
