from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CaptureError(Exception):
    """Base class for capture-related errors."""


class CaptureReadError(CaptureError):
    """Error reading capture data."""


@dataclass
class Capture:
    """Represents a single captured request/response pair."""
    request: Dict[str, Any]
    response: Dict[str, Any]


class CaptureStore(ABC):
    """Abstract base class for capture storage backends."""
    
    @abstractmethod
    def save(self, capture: Capture) -> None:
        """Save a single capture."""
        pass

    @abstractmethod
    def list(self) -> List[Capture]:
        """List all saved captures."""
        pass


class InMemoryCaptureStore(CaptureStore):
    """Stores captures in memory."""
    
    def __init__(self) -> None:
        self._caps: List[Capture] = []

    def save(self, capture: Capture) -> None:
        self._caps.append(capture)

    def list(self) -> List[Capture]:
        return list(self._caps)


class JSONFileCaptureStore(CaptureStore):
    """Stores captures in a JSON Lines file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, capture: Capture) -> None:
        """Appends a capture to the file as a JSON object."""
        with self.path.open("a", encoding="utf-8") as f:
            json.dump(asdict(capture), f)
            f.write("\n")

    def list(self) -> List[Capture]:
        """Reads all captures from the file."""
        if not self.path.exists():
            return []
        
        captures = []
        with self.path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        captures.append(Capture(request=data["request"], response=data["response"]))
                    except json.JSONDecodeError as e:
                        msg = f"Failed to decode JSON at line {i} in {self.path}: {e}"
                        logger.error(msg)
                        raise CaptureReadError(msg) from e
                    except KeyError as e:
                        msg = f"Missing required field at line {i} in {self.path}: {e}"
                        logger.error(msg)
                        raise CaptureReadError(msg) from e
        return captures
