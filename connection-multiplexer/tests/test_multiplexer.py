import random
import pytest

from connection_multiplexer import ConnectionMultiplexer, MultiplexingError, SimulatedTransport


def test_failover_on_drop(monkeypatch):
    random.seed(0)
    mux = ConnectionMultiplexer()
    dropping = SimulatedTransport("primary", drop_rate=1.0, base_latency_ms=0, jitter_ms=0)
    healthy = SimulatedTransport("secondary", drop_rate=0.0, base_latency_ms=0, jitter_ms=0)

    mux.register("primary", dropping, priority=1)
    mux.register("secondary", healthy, priority=2)

    response = mux.send({"msg": "hello"})
    assert response["via"] == "secondary"
    assert "primary" in response["attempted"]


def test_priority_preferred_when_healthy():
    random.seed(1)
    mux = ConnectionMultiplexer()
    primary = SimulatedTransport("primary", drop_rate=0.0, base_latency_ms=0, jitter_ms=0)
    backup = SimulatedTransport("backup", drop_rate=0.0, base_latency_ms=0, jitter_ms=0)

    mux.register("primary", primary, priority=1)
    mux.register("backup", backup, priority=2)

    response = mux.send({"msg": "hi"})
    assert response["via"] == "primary"


def test_no_transport_available_raises():
    mux = ConnectionMultiplexer()
    with pytest.raises(MultiplexingError):
        mux.send("payload")


def test_register_validates_name():
    """Test that registration validates transport name."""
    mux = ConnectionMultiplexer()
    transport = SimulatedTransport("test")
    
    with pytest.raises(ValueError, match="name must not be empty"):
        mux.register("", transport)
    
    with pytest.raises(ValueError, match="name must not be empty"):
        mux.register("   ", transport)


def test_register_validates_weight():
    """Test that registration validates weight."""
    mux = ConnectionMultiplexer()
    transport = SimulatedTransport("test")
    
    with pytest.raises(ValueError, match="weight must be positive"):
        mux.register("test", transport, weight=-1.0)
    
    with pytest.raises(ValueError, match="weight must be positive"):
        mux.register("test", transport, weight=0.0)


def test_send_rejects_none_payload():
    """Test that send rejects None payload."""
    mux = ConnectionMultiplexer()
    transport = SimulatedTransport("test", drop_rate=0.0)
    mux.register("test", transport)
    
    with pytest.raises(ValueError, match="Payload cannot be None"):
        mux.send(None)


def test_duplicate_registration_replaces():
    """Test that re-registering same name replaces old entry."""
    random.seed(42)
    mux = ConnectionMultiplexer()
    t1 = SimulatedTransport("t1", drop_rate=1.0)  # will always drop
    t2 = SimulatedTransport("t1", drop_rate=0.0)  # will always succeed
    
    mux.register("t1", t1)
    mux.register("t1", t2)  # Replace
    
    response = mux.send({"msg": "test"})
    assert response["via"] == "t1"
    assert response["result"]["transport"] == "t1"


def test_unregister_removes_transport():
    """Test transport unregistration."""
    mux = ConnectionMultiplexer()
    transport = SimulatedTransport("test")
    mux.register("test", transport)
    mux.unregister("test")
    
    with pytest.raises(MultiplexingError):
        mux.send("payload")


def test_health_monitoring():
    """Test transport health score tracking."""
    mux = ConnectionMultiplexer()
    transport = SimulatedTransport("test")
    mux.register("test", transport)
    
    health = mux.heartbeat()
    assert "test" in health
    assert 0.0 <= health["test"] <= 1.0


def test_close_cleanup():
    """Test proper cleanup on close."""
    mux = ConnectionMultiplexer()
    transport = SimulatedTransport("test")
    mux.register("test", transport)
    mux.close()
    
    with pytest.raises(MultiplexingError):
        mux.send("payload")
