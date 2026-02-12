from __future__ import annotations

import logging
import random
import time
import statistics
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Type, Optional

from .scenario import Scenario
from .exceptions import SimulatedFaultError

logger = logging.getLogger(__name__)


@dataclass
class ChaosResult:
    successes: int = 0
    failures: int = 0
    dropped: int = 0
    durations: List[float] = field(default_factory=list)

    @property
    def total_requests(self) -> int:
        return self.successes + self.failures + self.dropped

    @property
    def avg_latency_ms(self) -> float:
        if not self.durations:
            return 0.0
        return statistics.mean(self.durations) * 1000

    def _percentile(self, p: float) -> float:
        if not self.durations:
            return 0.0
        # Python 3.8+ has statistics.quantiles, but let's be safe for exact percentiles
        # or just use quantiles if we are on 3.10 as per pyproject.toml
        try:
            return statistics.quantiles(self.durations, n=100)[int(p * 100) - 1] * 1000
        except statistics.StatisticsError:
            return 0.0

    @property
    def p50_ms(self) -> float:
        return self._percentile(0.50)

    @property
    def p90_ms(self) -> float:
        return self._percentile(0.90)

    @property
    def p99_ms(self) -> float:
        return self._percentile(0.99)


class ChaosRunner:
    def __init__(self, scenario: Scenario, fault_exception_cls: Type[Exception] = SimulatedFaultError):
        self.scenario = scenario
        self.fault_exception_cls = fault_exception_cls
        self._tokens: Deque[float] = deque()
        self._last_refill = time.time()

    def _throttle(self) -> None:
        if not self.scenario.throttle_rps:
            return
        
        # Token bucket algorithm
        now = time.time()
        elapsed = now - self._last_refill
        
        # Add tokens based on elapsed time
        new_tokens = self.scenario.throttle_rps * elapsed
        if new_tokens > 0:
            for _ in range(int(new_tokens)):
                self._tokens.append(now)
            self._last_refill = now
        
        # Cap tokens at 1 second worth of capacity (burst size)
        max_tokens = int(self.scenario.throttle_rps)
        while len(self._tokens) > max_tokens:
            self._tokens.popleft()

        if not self._tokens:
            # We are empty, sleep until we can get a token
            # Time to next token = 1 / rps
            sleep_time = 1.0 / self.scenario.throttle_rps
            logger.debug(f"Throttling for {sleep_time:.4f}s")
            time.sleep(sleep_time)
            # After sleeping, we technically "earned" a token and "spent" it immediately
            self._last_refill = time.time()
        else:
            # Consume a token
            self._tokens.pop()

    def run(self, func: Callable[..., Any], *args: Any, iterations: int = 1, **kwargs: Any) -> ChaosResult:
        logger.info(f"Starting chaos run: iterations={iterations}, scenario={self.scenario}")
        result = ChaosResult()
        deadline = None
        if self.scenario.duration_limit_sec:
            deadline = time.time() + self.scenario.duration_limit_sec

        for i in range(iterations):
            if deadline and time.time() > deadline:
                logger.info("Duration limit reached, stopping early.")
                break

            self._throttle()

            # Drop logic
            if self.scenario.drop_rate > 0 and random.random() < self.scenario.drop_rate:
                logger.debug("Request dropped")
                result.dropped += 1
                continue

            # Latency logic
            latency = self.scenario.latency_ms
            if self.scenario.jitter_ms > 0:
                # uniform between -jitter and +jitter
                jitter = random.uniform(-self.scenario.jitter_ms, self.scenario.jitter_ms)
                latency += jitter
            
            # Ensure latency is not negative
            latency = max(0.0, latency)

            start = time.time()
            if latency > 0:
                time.sleep(latency / 1000.0)

            try:
                # Fault logic
                if self.scenario.fault_rate > 0 and random.random() < self.scenario.fault_rate:
                    logger.debug("Injecting fault")
                    raise self.fault_exception_cls("Injected fault via ChaosRunner")
                
                func(*args, **kwargs)
                result.successes += 1
            except Exception as e:
                # We catch ALL exceptions here to count them as failures during the run
                # This includes the injected fault if it wasn't caught by func
                result.failures += 1
                # Log only if it's NOT our injected fault (unless we want verbose logs)
                if not isinstance(e, self.fault_exception_cls):
                     logger.debug(f"Operation failed with exception: {e}")
            finally:
                result.durations.append(time.time() - start)

        logger.info(f"Run complete: {result}")
        return result
