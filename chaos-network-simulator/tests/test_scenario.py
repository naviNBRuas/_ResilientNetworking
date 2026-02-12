import pytest
import json
import tempfile
import os
from chaos_network_simulator import Scenario, ChaosConfigurationError

def test_scenario_defaults():
    s = Scenario()
    assert s.latency_ms == 0.0
    assert s.drop_rate == 0.0
    assert s.fault_rate == 0.0

def test_scenario_validation_latency():
    with pytest.raises(ValueError, match="latency_ms"):
        Scenario(latency_ms=-1.0)

def test_scenario_validation_probabilities():
    with pytest.raises(ValueError, match="drop_rate"):
        Scenario(drop_rate=1.1)
    with pytest.raises(ValueError, match="drop_rate"):
        Scenario(drop_rate=-0.1)
    with pytest.raises(ValueError, match="fault_rate"):
        Scenario(fault_rate=1.1)

def test_scenario_json_serialization():
    s = Scenario(latency_ms=100, drop_rate=0.1)
    json_str = s.to_json()
    data = json.loads(json_str)
    assert data["latency_ms"] == 100
    assert data["drop_rate"] == 0.1
    
    s2 = Scenario.from_json(json_str)
    assert s2 == s

def test_scenario_file_io():
    s = Scenario(latency_ms=50, fault_rate=0.01)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    
    try:
        s.to_json(path)
        s2 = Scenario.from_json(path)
        assert s2 == s
    finally:
        os.unlink(path)
