
import time
from unittest.mock import patch
import pytest
from adaptive_retry_strategy.circuit_breaker import CircuitBreaker, CircuitState

class TestCircuitBreaker:
    def test_state_transitions(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10, success_threshold=2)
        
        # CLOSED -> OPEN
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # OPEN -> HALF_OPEN
        with patch("time.time", return_value=time.time() + 11):
             # First call triggers state check/transition logic in allow_request
             assert cb.allow_request() is True
             assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_threshold(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10, success_threshold=2)
        cb.record_failure() # OPEN
        
        with patch("time.time", return_value=time.time() + 11):
            assert cb.allow_request() is True # HALF_OPEN
            
            # 1st success
            cb.record_success()
            assert cb.state == CircuitState.HALF_OPEN # Not closed yet
            
            # 2nd success
            cb.record_success()
            assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reset(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10, success_threshold=2)
        cb.record_failure() # OPEN
        
        with patch("time.time", return_value=time.time() + 11):
            cb.allow_request() # HALF_OPEN
            
            cb.record_success() # 1/2 successes
            assert cb.state == CircuitState.HALF_OPEN
            
            cb.record_failure() # Fail!
            assert cb.state == CircuitState.OPEN
