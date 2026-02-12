import pytest
from config_rollout import (
    ConfigLoader,
    FeatureFlag,
    RolloutEngine,
    ConfigError,
    RolloutError,
    parse_feature_flags,
)


# --- ConfigLoader Tests ---

def test_config_loader_parses_json():
    loader = ConfigLoader()
    cfg = loader.load('{"a": 1, "b": "test"}')
    assert cfg["a"] == 1
    assert cfg["b"] == "test"


def test_config_loader_invalid_json():
    loader = ConfigLoader()
    with pytest.raises(ConfigError, match="Failed to parse config JSON"):
        loader.load('{"a": 1')  # Missing closing brace


def test_config_loader_from_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"foo": "bar"}', encoding="utf-8")
    
    loader = ConfigLoader()
    cfg = loader.load_from_file(config_file)
    assert cfg["foo"] == "bar"


def test_config_loader_file_not_found():
    loader = ConfigLoader()
    with pytest.raises(ConfigError, match="Failed to read config file"):
        loader.load_from_file("non_existent_file.json")


# --- FeatureFlag Tests ---

def test_feature_flag_validation():
    with pytest.raises(RolloutError, match="must be between 0 and 100"):
        FeatureFlag(name="bad", percentage=101.0)
    
    with pytest.raises(RolloutError, match="must be between 0 and 100"):
        FeatureFlag(name="bad", percentage=-1.0)

    # These should pass
    FeatureFlag(name="good", percentage=0.0)
    FeatureFlag(name="good", percentage=100.0)


def test_feature_flag_from_dict():
    flag = FeatureFlag.from_dict("test", {"percentage": 25.5})
    assert flag.name == "test"
    assert flag.percentage == 25.5
    
    # Defaults
    flag_default = FeatureFlag.from_dict("default", {})
    assert flag_default.percentage == 0.0

    # Errors
    with pytest.raises(RolloutError, match="Invalid configuration"):
        FeatureFlag.from_dict("bad", {"percentage": "not-a-number"})


# --- Parsing Tests ---

def test_parse_feature_flags():
    config = {
        "flag1": {"percentage": 10},
        "flag2": {"percentage": 20},
        "not_a_flag": "ignore_me"
    }
    flags = parse_feature_flags(config)
    
    assert len(flags) == 2
    assert flags["flag1"].percentage == 10.0
    assert flags["flag2"].percentage == 20.0
    assert "not_a_flag" not in flags


# --- RolloutEngine Tests ---

def test_rollout_missing_flag():
    engine = RolloutEngine({})
    assert engine.enabled("non_existent") is False


def test_rollout_always_enabled():
    flags = {"always": FeatureFlag(name="always", percentage=100.0)}
    engine = RolloutEngine(flags)
    assert engine.enabled("always", identifier="user1") is True
    assert engine.enabled("always", identifier="user2") is True
    assert engine.enabled("always") is True  # Random fallback


def test_rollout_always_disabled():
    flags = {"never": FeatureFlag(name="never", percentage=0.0)}
    engine = RolloutEngine(flags)
    assert engine.enabled("never", identifier="user1") is False
    assert engine.enabled("never", identifier="user2") is False
    assert engine.enabled("never") is False  # Random fallback


def test_rollout_determinism():
    flags = {"fifty": FeatureFlag(name="fifty", percentage=50.0)}
    engine = RolloutEngine(flags)
    
    # Same user should always get same result
    result1 = engine.enabled("fifty", identifier="user_consistent")
    result2 = engine.enabled("fifty", identifier="user_consistent")
    assert result1 == result2

    # Verify that different users MIGHT get different results (statistically likely)
    # This is a weak test but ensures we aren't just returning True/False for everyone
    # We check a set of users and expect mixed results
    results = [engine.enabled("fifty", identifier=f"user_{i}") for i in range(100)]
    assert True in results
    assert False in results


def test_rollout_distribution():
    # Statistical test: with 50% rollout, roughly 50% of 1000 users should be enabled
    flags = {"check": FeatureFlag(name="check", percentage=50.0)}
    engine = RolloutEngine(flags)
    
    count = sum(1 for i in range(1000) if engine.enabled("check", identifier=f"u{i}"))
    
    # Allow a margin of error (e.g., 400-600)
    assert 400 <= count <= 600