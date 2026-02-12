import pytest
from unittest.mock import MagicMock, patch, call
from adaptive_retry_strategy import (
    RetryEngine,
    RetryPolicy,
    ExponentialBackoff,
    CircuitBreaker,
)

class TestRetryEngine:
    """Test retry execution engine."""

    def test_successful_operation(self):
        """Test that successful operation doesn't retry."""
        policy = RetryPolicy(max_attempts=3)
        engine = RetryEngine(policy)
        
        func = MagicMock(return_value={"success": True})
        
        result = engine.run(func)
        
        assert result.succeeded is True
        assert result.attempts == 1
        assert result.result == {"success": True}
        func.assert_called_once()

    def test_retry_on_failure(self):
        """Test basic retry mechanism."""
        policy = RetryPolicy(max_attempts=3, backoff=ExponentialBackoff(base=0.1, jitter=0.0))
        engine = RetryEngine(policy)
        
        func = MagicMock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), "Success"])
        
        with patch("time.sleep") as mock_sleep:
            result = engine.run(func)
        
        assert result.succeeded is True
        assert result.attempts == 3
        assert result.result == "Success"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2 # Sleep after attempt 1 and 2

    def test_max_attempts_exceeded(self):
        """Test that retries are bounded by max_attempts."""
        policy = RetryPolicy(max_attempts=3, backoff=ExponentialBackoff(base=0.1, jitter=0.0))
        engine = RetryEngine(policy)
        
        func = MagicMock(side_effect=ValueError("Always fails"))
        
        with patch("time.sleep") as mock_sleep:
            result = engine.run(func)
        
        assert result.succeeded is False
        assert result.attempts == 3
        assert isinstance(result.error, ValueError)
        
        # KEY FIX VERIFICATION: Should sleep 2 times (after attempt 1 and 2), not 3.
        assert mock_sleep.call_count == 2 

    def test_non_retriable_exception(self):
        """Test that non-retriable exceptions aren't retried."""
        policy = RetryPolicy(max_attempts=5, retry_on=(ValueError,))
        engine = RetryEngine(policy)
        
        func = MagicMock(side_effect=TypeError("Not retriable"))
        
        with pytest.raises(TypeError):
            engine.run(func)
        
        assert func.call_count == 1

    def test_circuit_breaker_integration(self):
        """Test that circuit breaker affects retry behavior."""
        circuit_breaker = CircuitBreaker(failure_threshold=2)
        policy = RetryPolicy(max_attempts=5, backoff=ExponentialBackoff(base=0.1))
        engine = RetryEngine(policy, circuit_breaker=circuit_breaker)
        
        func = MagicMock(side_effect=ValueError("Fail"))
        
        with patch("time.sleep"):
            result = engine.run(func)
        
        # Should attempt 1 (fail), attempt 2 (fail -> CB OPEN), attempt 3 (CB blocks)
        # Wait, if CB opens on attempt 2 failure, does attempt 3 happen?
        # Logic:
        # Loop 1: Call -> Fail -> Record Failure (1/2). Sleep.
        # Loop 2: Call -> Fail -> Record Failure (2/2 -> OPEN). Sleep.
        # Loop 3: Check Allow -> False. Return Error.
        
        # So we expect 2 actual calls to func.
        assert func.call_count == 2
        assert result.attempts == 2 # 2 actual attempts made
        assert result.succeeded is False
        # The result error should be the last error or "circuit-open"?
        # Loop 3 returns RetryOutcome(error=RuntimeError("circuit-open"))
        assert isinstance(result.error, RuntimeError)
        assert str(result.error) == "circuit-open"

    def test_system_signals_ignored_by_default(self):
        """Test that KeyboardInterrupt propagates and doesn't trigger retry."""
        policy = RetryPolicy(max_attempts=3)
        engine = RetryEngine(policy)
        
        func = MagicMock(side_effect=KeyboardInterrupt("Stop"))
        
        with pytest.raises(KeyboardInterrupt):
            engine.run(func)
        
        assert func.call_count == 1 # Should not retry