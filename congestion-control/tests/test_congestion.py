import time
import pytest
from unittest.mock import patch, Mock
from congestion_control import AdaptiveCongestionController, TokenBucket

# --- TokenBucket Tests ---

def test_token_bucket_init_defaults():
    bucket = TokenBucket(rate=10, capacity=20)
    assert bucket.rate == 10
    assert bucket.capacity == 20
    assert bucket.tokens == 20  # defaults to capacity
    assert bucket.last is not None

def test_token_bucket_invalid_init():
    with pytest.raises(ValueError):
        TokenBucket(rate=-1, capacity=10)
    with pytest.raises(ValueError):
        TokenBucket(rate=10, capacity=0)

@patch('time.monotonic')
def test_token_bucket_allow_logic(mock_time):
    mock_time.return_value = 0.0
    bucket = TokenBucket(rate=1, capacity=5)
    
    # Initially full (5 tokens)
    assert bucket.allow(5.0) is True
    assert bucket.tokens == 0.0
    
    # Now empty, immediate request fails
    assert bucket.allow(1.0) is False
    
    # Advance time by 1 second -> +1 token
    mock_time.return_value = 1.0
    assert bucket.allow(1.0) is True
    assert bucket.tokens == 0.0
    
    # Advance time by 10 seconds -> capped at capacity (5)
    mock_time.return_value = 11.0
    bucket.allow(0.0) # Trigger refill without consuming
    assert bucket.tokens == 5.0

@patch('time.monotonic')
def test_token_bucket_partial_refill(mock_time):
    mock_time.return_value = 0.0
    bucket = TokenBucket(rate=10, capacity=10)
    bucket.tokens = 0.0 # start empty
    
    mock_time.return_value = 0.1 # 0.1s * 10/s = 1 token
    assert bucket.allow(1.0) is True

def test_token_bucket_thread_safety_smoke():
    # Just verify it doesn't crash under simple concurrency
    import threading
    bucket = TokenBucket(rate=1000, capacity=1000)
    
    def worker():
        for _ in range(100):
            bucket.allow()
            
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    # No assertions on exact count as it depends on timing, but ensures no deadlock/crash

# --- AdaptiveCongestionController Tests ---

def test_adaptive_init():
    bucket = TokenBucket(rate=10, capacity=10)
    ctrl = AdaptiveCongestionController(bucket)
    assert ctrl.min_rate == 1.0
    assert ctrl.max_rate == 1000.0

@patch('time.monotonic')
def test_adaptive_on_success_increases_rate(mock_time):
    mock_time.return_value = 100.0
    bucket = TokenBucket(rate=10, capacity=100)
    ctrl = AdaptiveCongestionController(bucket, increase_factor=1.5, max_rate=100)
    
    ctrl.on_success(rtt_ms=50)
    assert bucket.rate == 15.0 # 10 * 1.5

    # Test Max Rate Cap
    bucket.rate = 90
    ctrl.on_success(rtt_ms=50)
    assert bucket.rate == 100 # capped at max

@patch('time.monotonic')
def test_adaptive_on_success_high_latency(mock_time):
    mock_time.return_value = 100.0
    bucket = TokenBucket(rate=10, capacity=100)
    ctrl = AdaptiveCongestionController(bucket, high_latency_threshold=200)
    
    # Latency > threshold -> no increase
    ctrl.on_success(rtt_ms=300)
    assert bucket.rate == 10.0

@patch('time.monotonic')
def test_adaptive_on_congestion_decreases_rate(mock_time):
    mock_time.return_value = 100.0
    bucket = TokenBucket(rate=20, capacity=100)
    ctrl = AdaptiveCongestionController(bucket, decrease_factor=0.5, min_rate=5)
    
    ctrl.on_congestion_signal()
    assert bucket.rate == 10.0 # 20 * 0.5
    
    # Test Min Rate Floor
    ctrl.on_congestion_signal() # -> 5.0
    ctrl.on_congestion_signal() # -> 2.5 but floored at 5
    assert bucket.rate == 5.0

def test_adaptive_allow_delegates():
    bucket = Mock(spec=TokenBucket)
    ctrl = AdaptiveCongestionController(bucket)
    
    ctrl.allow(cost=2.0)
    bucket.allow.assert_called_with(2.0)