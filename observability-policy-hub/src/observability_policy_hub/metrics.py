from __future__ import annotations

import threading
import time
from collections import deque
from typing import Dict, List, Any


class MetricRegistry:
    """
    A thread-safe metrics registry supporting counters, gauges, and histograms.
    
    Attributes:
        counters (Dict[str, int]): Stores cumulative counts.
        gauges (Dict[str, float]): Stores instantaneous values.
        histograms (Dict[str, deque]): Stores a sliding window of recent observations.
    """

    def __init__(self, histogram_window_size: int = 1000):
        """
        Initialize the MetricRegistry.

        Args:
            histogram_window_size (int): Maximum number of samples to keep for histograms.
                                         Defaults to 1000.
        """
        self._lock = threading.RLock()
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = {}
        self._histogram_window_size = histogram_window_size

    def inc(self, name: str, value: int = 1) -> None:
        """
        Increment a counter by the given value.

        Args:
            name (str): The name of the counter.
            value (int): The value to increment by. Defaults to 1.
        """
        with self._lock:
            if name not in self.counters:
                self.counters[name] = 0
            self.counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge to a specific value.

        Args:
            name (str): The name of the gauge.
            value (float): The value to set.
        """
        with self._lock:
            self.gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        """
        Record a value in a histogram.

        Args:
            name (str): The name of the histogram.
            value (float): The value to record.
        """
        with self._lock:
            if name not in self.histograms:
                self.histograms[name] = deque(maxlen=self._histogram_window_size)
            self.histograms[name].append(value)

    def summary(self) -> Dict[str, Any]:
        """
        Return a snapshot of all metrics.

        Returns:
            Dict[str, Any]: A dictionary containing counters, gauges, and histogram summaries.
        """
        with self._lock:
            # Create a deep copy or representation while holding the lock
            counters_snapshot = dict(self.counters)
            gauges_snapshot = dict(self.gauges)
            
            histograms_snapshot = {}
            for name, values in self.histograms.items():
                count = len(values)
                if count > 0:
                    sorted_values = sorted(values)
                    avg = sum(values) / count
                    # simple percentile calculation
                    p50 = sorted_values[int(0.50 * count)]
                    p95 = sorted_values[int(0.95 * count)]
                    p99 = sorted_values[int(0.99 * count)]
                    histograms_snapshot[name] = {
                        "count": count,
                        "avg": avg,
                        "p50": p50,
                        "p95": p95,
                        "p99": p99,
                    }
                else:
                    histograms_snapshot[name] = {
                        "count": 0,
                        "avg": 0.0,
                        "p50": 0.0,
                        "p95": 0.0,
                        "p99": 0.0,
                    }

            return {
                "counters": counters_snapshot,
                "gauges": gauges_snapshot,
                "histograms": histograms_snapshot,
            }