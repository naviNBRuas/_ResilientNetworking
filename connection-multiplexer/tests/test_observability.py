import logging
from typing import Any, Dict
from connection_multiplexer import ConnectionMultiplexer, SimulatedTransport

def test_observability_callbacks():
    events = []

    def on_event(name: str, data: Dict[str, Any]):
        events.append((name, data))

    mux = ConnectionMultiplexer(on_event=on_event)
    t1 = SimulatedTransport("t1", base_latency_ms=0)
    mux.register("t1", t1)

    mux.send("hello")

    assert len(events) >= 2
    assert events[0][0] == "send_attempt"
    assert events[0][1]["transport"] == "t1"
    assert events[1][0] == "send_success"
    assert events[1][1]["transport"] == "t1"

def test_observability_failure():
    events = []

    def on_event(name: str, data: Dict[str, Any]):
        events.append((name, data))

    mux = ConnectionMultiplexer(on_event=on_event)
    # Transport that always fails
    t1 = SimulatedTransport("t1", drop_rate=1.0)
    mux.register("t1", t1)

    try:
        mux.send("hello")
    except Exception:
        pass

    # Expect: attempt -> transport_failure -> multiplex_failure
    names = [e[0] for e in events]
    assert "send_attempt" in names
    assert "transport_failure" in names
    assert "multiplex_failure" in names
