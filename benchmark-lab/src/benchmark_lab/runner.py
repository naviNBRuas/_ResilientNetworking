from __future__ import annotations

import gc
import math
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable, List


@dataclass
class BenchmarkResult:
    """Stores and analyzes benchmark execution times."""
    
    samples: List[float]

    @property
    def total_time(self) -> float:
        """Total execution time of all samples in seconds."""
        return sum(self.samples)

    @property
    def min_ms(self) -> float:
        """Minimum execution time in milliseconds."""
        return min(self.samples) * 1000 if self.samples else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum execution time in milliseconds."""
        return max(self.samples) * 1000 if self.samples else 0.0

    @property
    def avg_ms(self) -> float:
        """Average execution time in milliseconds."""
        return statistics.mean(self.samples) * 1000 if self.samples else 0.0

    @property
    def median_ms(self) -> float:
        """Median execution time in milliseconds."""
        return statistics.median(self.samples) * 1000 if self.samples else 0.0

    @property
    def stddev_ms(self) -> float:
        """Standard deviation of execution time in milliseconds."""
        if len(self.samples) < 2:
            return 0.0
        return statistics.stdev(self.samples) * 1000

    @property
    def p95_ms(self) -> float:
        """95th percentile execution time in milliseconds."""
        return self._percentile(95)

    @property
    def p99_ms(self) -> float:
        """99th percentile execution time in milliseconds."""
        return self._percentile(99)
    
    def _percentile(self, percentile: float) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int((percentile / 100.0) * len(sorted_samples))
        # Clamp index to valid range
        idx = min(idx, len(sorted_samples) - 1)
        return sorted_samples[idx] * 1000

    def __str__(self) -> str:
        if not self.samples:
            return "BenchmarkResult(No samples)"
        return (
            f"BenchmarkResult(\n"
            f"  samples={len(self.samples)},\n"
            f"  avg={self.avg_ms:.4f} ms,\n"
            f"  min={self.min_ms:.4f} ms,\n"
            f"  max={self.max_ms:.4f} ms,\n"
            f"  median={self.median_ms:.4f} ms,\n"
            f"  p95={self.p95_ms:.4f} ms,\n"
            f"  p99={self.p99_ms:.4f} ms,\n"
            f"  stddev={self.stddev_ms:.4f} ms\n"
            f")"
        )


class BenchmarkRunner:
    """Executes benchmarks with configurable warmup and garbage collection settings."""

    def __init__(self, iterations: int = 1000, warmup: int = 5, disable_gc: bool = False):
        """
        Initialize the runner.

        Args:
            iterations: Number of measurement iterations to run.
            warmup: Number of warmup iterations to run before measurement (discarded).
            disable_gc: If True, disables garbage collection during the measurement phase.
        """
        if iterations <= 0:
            raise ValueError("Iterations must be greater than 0")
        if warmup < 0:
            raise ValueError("Warmup must be non-negative")

        self.iterations = iterations
        self.warmup = warmup
        self.disable_gc = disable_gc

    def run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> BenchmarkResult:
        """
        Run the benchmark for the given function.

        Args:
            fn: The function to benchmark.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            BenchmarkResult containing the timing samples.
        """
        # Warmup phase
        for _ in range(self.warmup):
            fn(*args, **kwargs)

        # Measurement phase
        samples: List[float] = []
        gc_enabled = gc.isenabled()
        
        try:
            if self.disable_gc:
                gc.disable()
            
            for _ in range(self.iterations):
                start = time.perf_counter()
                fn(*args, **kwargs)
                end = time.perf_counter()
                samples.append(end - start)
        finally:
            if self.disable_gc and gc_enabled:
                gc.enable()

        return BenchmarkResult(samples=samples)
