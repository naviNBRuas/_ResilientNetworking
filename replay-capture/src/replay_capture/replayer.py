from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .capture import Capture, CaptureStore

logger = logging.getLogger(__name__)


@dataclass
class ReplayFailure:
    """Details about a failed replay attempt."""
    capture: Capture
    actual_response: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

    def __str__(self) -> str:
        if self.error:
            return f"Error: {self.error}"
        return f"Mismatch: Expected {self.capture.response}, got {self.actual_response}"


@dataclass
class ReplayResult:
    """Aggregated results of a replay session."""
    successes: int = 0
    failures: List[ReplayFailure] = field(default_factory=list)

    @property
    def total_runs(self) -> int:
        return self.successes + len(self.failures)

    @property
    def failure_count(self) -> int:
        return len(self.failures)


class Replayer:
    """Executes captures against a handler function."""
    
    def __init__(self, store: CaptureStore) -> None:
        self.store = store

    def replay(
        self, 
        handler: Callable[[Dict[str, Any]], Dict[str, Any]], 
        stop_on_failure: bool = False
    ) -> ReplayResult:
        """
        Replays all captures in the store against the provided handler.
        
        Args:
            handler: A function that takes a request dict and returns a response dict.
            stop_on_failure: If True, stops replaying after the first failure.
            
        Returns:
            ReplayResult containing statistics and failure details.
        """
        result = ReplayResult()
        captures = self.store.list()
        total = len(captures)
        
        logger.info(f"Starting replay of {total} captures.")
        
        for i, cap in enumerate(captures, 1):
            try:
                # Deepcopy to prevent handler from mutating the stored request
                req_copy = copy.deepcopy(cap.request)
                resp = handler(req_copy)
                
                if resp == cap.response:
                    result.successes += 1
                    logger.debug(f"Capture {i}/{total} passed.")
                else:
                    failure = ReplayFailure(capture=cap, actual_response=resp)
                    result.failures.append(failure)
                    logger.warning(f"Capture {i}/{total} failed: {failure}")
                    if stop_on_failure:
                        logger.info("Stopping replay due to failure.")
                        break
            except Exception as e:
                failure = ReplayFailure(capture=cap, error=e)
                result.failures.append(failure)
                logger.error(f"Capture {i}/{total} error: {e}", exc_info=True)
                if stop_on_failure:
                    logger.info("Stopping replay due to error.")
                    break
                    
        logger.info(f"Replay finished. Success: {result.successes}, Failures: {result.failure_count}")
        return result
