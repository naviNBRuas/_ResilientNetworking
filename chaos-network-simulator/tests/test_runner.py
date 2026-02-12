import random
import time
from unittest.mock import patch, MagicMock
import pytest

from chaos_network_simulator import ChaosRunner, Scenario, ChaosResult, SimulatedFaultError

class CustomError(Exception):
    pass

def test_result_stats():
    # Manual durations to test percentiles
    r = ChaosResult()
    # 0.0 to 0.100s (0 to 100ms)
    r.durations = [i / 1000.0 for i in range(100)]
    # p50 should be ~50ms, p90 ~90ms, p99 ~99ms
    # Using statistics.quantiles (exclusive), exact values might vary slightly depending on method
    # but roughly correct.
    assert 49.0 <= r.p50_ms <= 51.0
    assert 89.0 <= r.p90_ms <= 91.0
    assert 98.0 <= r.p99_ms <= 100.0
    assert r.avg_latency_ms == 49.5

def test_drop_rate():
    random.seed(42)
    scenario = Scenario(drop_rate=1.0)
    runner = ChaosRunner(scenario)
    result = runner.run(lambda: None, iterations=10)
    assert result.dropped == 10
    assert result.successes == 0
    assert result.failures == 0

def test_fault_rate_default_exception():
    random.seed(42)
    scenario = Scenario(fault_rate=1.0)
    runner = ChaosRunner(scenario)
    
    # We expect failures
    result = runner.run(lambda: None, iterations=10)
    assert result.failures == 10
    assert result.successes == 0
    assert result.dropped == 0

def test_fault_rate_custom_exception():
    random.seed(42)
    scenario = Scenario(fault_rate=1.0)
    runner = ChaosRunner(scenario, fault_exception_cls=CustomError)
    
    # Pass a func that checks the exception type if possible, 
    # but runner catches it.
    # To verify the exception type, we can mock the func to ensure it's NOT called 
    # (since fault happens before func call in current impl? No, check logic).
    
    # Logic:
    # try:
    #   if random < fault_rate: raise Fault
    #   func()
    
    mock_func = MagicMock()
    result = runner.run(mock_func, iterations=5)
    
    assert result.failures == 5
    mock_func.assert_not_called()

def test_latency_jitter():
    # Mock time.sleep to verify calls
    scenario = Scenario(latency_ms=100, jitter_ms=0) # Fixed 100ms
    runner = ChaosRunner(scenario)
    
    with patch("time.sleep") as mock_sleep:
        runner.run(lambda: None, iterations=1)
        mock_sleep.assert_called_with(0.1)

def test_throttling():
    # 10 RPS -> 0.1s per token
    scenario = Scenario(throttle_rps=10)
    runner = ChaosRunner(scenario)
    
    start_time = time.time()
    # Run 11 requests. 
    # 1st consumes existing token? Or starts empty?
    # Runner init: _tokens empty. _last_refill = now.
    # _throttle calls:
    #   elapsed = 0.
    #   if not tokens: sleep(1/rps).
    # So first call sleeps 0.1s.
    # We want to verify it slows down.
    
    # Let's just run for a small number and check total duration
    # 5 iterations at 10 RPS should take at least 0.4s or so
    # (first might sleep, subsequent might burst if tokens accumulated? No, loop is tight).
    
    # Actually, simpler test:
    # If we request faster than RPS, we should sleep.
    
    with patch("time.sleep") as mock_sleep:
        runner.run(lambda: None, iterations=5)
        # Should have slept at least a few times
        assert mock_sleep.called
        # Verify arguments are roughly 0.1
        args, _ = mock_sleep.call_args
        # Depending on logic, might be slightly different, but roughly 1/RPS
        assert 0.09 < args[0] < 0.11

def test_duration_limit():
    scenario = Scenario(duration_limit_sec=0.1)
    runner = ChaosRunner(scenario)
    
    # Function takes 0.05s
    def slow_func():
        time.sleep(0.05)
        
    start = time.time()
    # Request 10 iterations (should take 0.5s), but limit is 0.1s
    result = runner.run(slow_func, iterations=10)
    duration = time.time() - start
    
    # Should stop early
    assert result.total_requests < 10
    assert duration < 0.3 # Allow some buffer