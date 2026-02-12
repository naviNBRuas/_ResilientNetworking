import logging
from sample_consumers.examples.client import ResilientClient

def test_client_success(caplog):
    """Test that the client successfully sends a message using the default stack."""
    caplog.set_level(logging.INFO)
    client = ResilientClient()
    client.send_message("Test Message")
    
    assert "Client: initiating send for 'Test Message'" in caplog.text
    assert "Multiplexer: Sending 'Test Message' via tcp..." in caplog.text
    assert "Client: Message delivered successfully." in caplog.text

def test_client_fallback_logic(caplog):
    """Test that the client falls back to the secondary protocol when primary fails."""
    caplog.set_level(logging.INFO)
    client = ResilientClient()
    
    # Configure to use a failing primary (UDP mock fails in our client.py)
    client.fallback.primary = "udp"
    client.fallback.fallback = "tcp"
    
    client.send_message("Fallback Test")
    
    # Check for failure logs of UDP
    assert "Multiplexer: UDP packet lost (simulated)" in caplog.text
    # Check for retry attempts (default max_retries=2)
    # We expect "RetryStrategy: Attempt 1 failed" ... "Attempt 2 failed"
    # Actually client.py mock retry logic logs "Attempt X failed"
    
    assert "RetryStrategy: Attempt 1 failed" in caplog.text
    
    # Check for fallback trigger
    assert "FallbackLayer: Downgrading to tcp" in caplog.text
    
    # Check for success on fallback
    assert "Multiplexer: Sending 'Fallback Test' via tcp..." in caplog.text
    assert "Client: Message delivered successfully." in caplog.text
