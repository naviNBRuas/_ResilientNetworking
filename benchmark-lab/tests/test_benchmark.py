import gc
import statistics
import time
from unittest.mock import MagicMock, patch

import pytest
from benchmark_lab import BenchmarkResult, BenchmarkRunner


def test_benchmark_result_stats():
    # 0.1s, 0.2s, ..., 1.0s
    samples = [i * 0.1 for i in range(1, 11)]
    result = BenchmarkResult(samples=samples)

    assert len(result.samples) == 10
    assert result.min_ms == pytest.approx(100.0)
    assert result.max_ms == pytest.approx(1000.0)
    assert result.avg_ms == pytest.approx(550.0)
    assert result.median_ms == pytest.approx(550.0)
    
    # Standard deviation of 1..10 is ~3.02765. Scaled by 0.1 is ~0.3027. In ms -> ~302.76
    expected_stddev = statistics.stdev(samples) * 1000
    assert result.stddev_ms == pytest.approx(expected_stddev)

    # p95 of 10 items: index 9 (last one) -> 1000.0 ms
    # p99 of 10 items: index 9 (last one) -> 1000.0 ms
    # Note: Logic in runner.py is straightforward index calculation.
    assert result.p95_ms == pytest.approx(1000.0) 
    assert result.p99_ms == pytest.approx(1000.0)

def test_benchmark_result_str():
    result = BenchmarkResult(samples=[0.1])
    s = str(result)
    assert "BenchmarkResult" in s
    assert "avg=" in s
    assert "min=" in s


def test_runner_basic():
    runner = BenchmarkRunner(iterations=10, warmup=0)
    result = runner.run(lambda: time.sleep(0.0001))
    assert len(result.samples) == 10
    assert result.avg_ms > 0.0


def test_runner_warmup():
    mock_func = MagicMock()
    runner = BenchmarkRunner(iterations=5, warmup=3)
    runner.run(mock_func)
    
    # Should be called 3 (warmup) + 5 (iterations) = 8 times
    assert mock_func.call_count == 8


def test_runner_disable_gc():
    with patch("gc.disable") as mock_disable, \
         patch("gc.enable") as mock_enable, \
         patch("gc.isenabled", return_value=True):
        
        runner = BenchmarkRunner(iterations=1, disable_gc=True)
        runner.run(lambda: None)
        
        mock_disable.assert_called_once()
        mock_enable.assert_called_once()


def test_runner_gc_restored_on_error():
    """Ensure GC is re-enabled even if the benchmarked function raises an exception."""
    with patch("gc.disable") as mock_disable, \
         patch("gc.enable") as mock_enable, \
         patch("gc.isenabled", return_value=True):
        
        # Set warmup=0 so we reach the try/finally block where gc.disable is called
        runner = BenchmarkRunner(iterations=1, warmup=0, disable_gc=True)
        
        with pytest.raises(RuntimeError):
            runner.run(lambda: (_ for _ in ()).throw(RuntimeError("Boom")))

        mock_disable.assert_called_once()
        mock_enable.assert_called_once()


def test_invalid_args():
    with pytest.raises(ValueError):
        BenchmarkRunner(iterations=0)
    with pytest.raises(ValueError):
        BenchmarkRunner(iterations=10, warmup=-1)
