import pytest
from unittest.mock import MagicMock
from sample_consumers.examples.client import ResilientClient

@pytest.fixture
def mock_deps():
    multiplexer = MagicMock()
    retry = MagicMock()
    fallback = MagicMock()
    
    # Configure retry to just call the function (pass-through) by default
    retry.execute.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
    
    # Configure fallback to just call the function with primary by default
    fallback.execute.side_effect = lambda func, payload: func(payload, "primary_proto")
    
    return multiplexer, retry, fallback

def test_client_init(mock_deps):
    mux, retry, fb = mock_deps
    client = ResilientClient(multiplexer=mux, retry_strategy=retry, fallback_layer=fb)
    assert client.multiplexer == mux
    assert client.retry == retry
    assert client.fallback == fb

def test_send_message_success(mock_deps):
    mux, retry, fb = mock_deps
    client = ResilientClient(multiplexer=mux, retry_strategy=retry, fallback_layer=fb)
    
    client.send_message("test_msg")
    
    # Verify fallback was called
    fb.execute.assert_called_once()
    
    # Verify retry was called (inside the lambda passed to fallback)
    # Since we mocked fallback to call the lambda, and retry to call the func...
    retry.execute.assert_called_once()
    
    # Verify multiplexer was called
    mux.send.assert_called_once_with("test_msg", protocol="primary_proto")

def test_send_message_total_failure(mock_deps):
    mux, retry, fb = mock_deps
    client = ResilientClient(multiplexer=mux, retry_strategy=retry, fallback_layer=fb)
    
    # Simulate failure in fallback layer (e.g. both protocols failed)
    fb.execute.side_effect = Exception("Total collapse")
    
    with pytest.raises(Exception, match="Total collapse"):
        client.send_message("doom")

def test_retry_integration_structure(mock_deps):
    """
    Verify that the function passed to fallback is indeed using retry.
    """
    mux, retry, fb = mock_deps
    client = ResilientClient(multiplexer=mux, retry_strategy=retry, fallback_layer=fb)
    
    # Capture the function passed to fallback
    def capture_func(func, payload):
        # Call it
        func(payload, "tcp")
        
    fb.execute.side_effect = capture_func
    
    client.send_message("msg")
    
    # Verify retry.execute was called with multiplexer.send
    retry.execute.assert_called_once()
    args, _ = retry.execute.call_args
    # args[0] should be multiplexer.send
    assert args[0] == mux.send
    assert args[1] == "msg"
