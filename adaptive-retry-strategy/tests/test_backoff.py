
import pytest
from adaptive_retry_strategy.backoff import ExponentialBackoff

class TestExponentialBackoff:
    """Test exponential backoff calculation."""

    def test_basic_backoff(self):
        """Test exponential backoff increases with attempts."""
        backoff = ExponentialBackoff(base=0.1, factor=2, max_delay=10.0, jitter=0.0)
        
        delays = [backoff.compute(i) for i in range(1, 5)]
        assert delays[0] == pytest.approx(0.1)  # 0.1
        assert delays[1] == pytest.approx(0.2)  # 0.1 * 2
        assert delays[2] == pytest.approx(0.4)  # 0.2 * 2
        assert delays[3] == pytest.approx(0.8)  # 0.4 * 2

    def test_max_delay_cap(self):
        """Test that backoff respects max_delay."""
        backoff = ExponentialBackoff(base=0.1, factor=2, max_delay=0.5, jitter=0.0)
        
        delay_4 = backoff.compute(4)
        assert delay_4 <= 0.5
        
    def test_jitter(self):
        """Test that jitter adds randomness."""
        backoff = ExponentialBackoff(base=1.0, factor=2, jitter=0.5)
        
        # We can't easily test randomness deterministically without seeding, 
        # but we can check bounds.
        delay = backoff.compute(1) # base=1.0
        # jitter 0.5 means range [0.5, 1.5]
        assert 0.5 <= delay <= 1.5
