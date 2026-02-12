import pytest
from unittest.mock import Mock, MagicMock
from protocol_fallback_layer.fallback_client import FallbackClient, FallbackResult
from protocol_fallback_layer.adapter import ProtocolAdapter
from protocol_fallback_layer.exceptions import AllAdaptersFailedError, NoCompatibleAdapterError
from protocol_fallback_layer.policy import PriorityListPolicy

class DummyAdapter(ProtocolAdapter):
    def __init__(self, name: str, *, supported: bool = True, fail: bool = False, fail_exception: Exception = None):
        self.name = name
        self._supported = supported
        self._fail = fail
        self._fail_exception = fail_exception or RuntimeError(f"{name} failed")

    def supports(self, capabilities):
        return self._supported

    def send(self, request, state):
        state.setdefault("history", []).append(self.name)
        if self._fail:
            raise self._fail_exception
        return f"{self.name}:{request}"

    def close(self, state):
        state["closed"] = True


def test_fallback_success_first_try():
    adapters = [
        DummyAdapter("primary", supported=True, fail=False),
        DummyAdapter("secondary", supported=True, fail=False),
    ]
    client = FallbackClient(adapters)
    result = client.send("test")
    
    assert result.chosen == "primary"
    assert result.response == "primary:test"
    assert result.attempted == ["primary"]
    assert client.state["history"] == ["primary"]


def test_fallback_skips_unsupported():
    adapters = [
        DummyAdapter("unsupported", supported=False),
        DummyAdapter("supported", supported=True, fail=False),
    ]
    client = FallbackClient(adapters)
    result = client.send("test")
    
    assert result.chosen == "supported"
    assert result.attempted == ["supported"]


def test_fallback_handles_failure_and_retries():
    adapters = [
        DummyAdapter("fail1", supported=True, fail=True),
        DummyAdapter("fail2", supported=True, fail=True),
        DummyAdapter("success", supported=True, fail=False),
    ]
    client = FallbackClient(adapters)
    result = client.send("test")
    
    assert result.chosen == "success"
    assert result.attempted == ["fail1", "fail2", "success"]
    assert "fail1" in result.errors
    assert "fail2" in result.errors
    assert client.state["history"] == ["fail1", "fail2", "success"]


def test_all_adapters_failed_exception():
    adapters = [
        DummyAdapter("fail1", supported=True, fail=True),
        DummyAdapter("fail2", supported=True, fail=True),
    ]
    client = FallbackClient(adapters)
    
    with pytest.raises(AllAdaptersFailedError) as excinfo:
        client.send("test")
    
    assert "fail1 failed" in str(excinfo.value)
    assert "fail2 failed" in str(excinfo.value)


def test_no_compatible_adapter_exception():
    adapters = [
        DummyAdapter("unsupported", supported=False),
    ]
    client = FallbackClient(adapters)
    
    with pytest.raises(NoCompatibleAdapterError):
        client.send("test")


def test_close_calls_adapters():
    mock_adapter = MagicMock(spec=ProtocolAdapter)
    mock_adapter.name = "mock"
    client = FallbackClient([mock_adapter])
    client.close()
    mock_adapter.close.assert_called_once_with(client.state)

def test_custom_policy():
    # Define a policy that reverses the order
    class ReversePolicy(PriorityListPolicy):
        def plan(self, adapters, capabilities):
            return reversed(list(super().plan(adapters, capabilities)))
            
    adapters = [
        DummyAdapter("first", supported=True, fail=True),
        DummyAdapter("second", supported=True, fail=False),
    ]
    
    client = FallbackClient(adapters, policy=ReversePolicy())
    result = client.send("test")
    
    # Because of reverse policy, 'second' is tried first.
    assert result.chosen == "second"
    assert result.attempted == ["second"]
    # 'first' should not be in history because 'second' succeeded
    assert client.state["history"] == ["second"]