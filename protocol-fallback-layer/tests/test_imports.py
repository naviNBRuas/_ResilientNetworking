from protocol_fallback_layer import (
    AllAdaptersFailedError,
    FallbackClient,
    FallbackPolicy,
    FallbackResult,
    NoCompatibleAdapterError,
    PriorityListPolicy,
    ProtocolAdapter,
    ProtocolFallbackError,
)


def test_top_level_imports():
    assert FallbackClient
    assert ProtocolAdapter
    assert FallbackResult
    assert FallbackPolicy
    assert PriorityListPolicy
    assert ProtocolFallbackError
    assert NoCompatibleAdapterError
    assert AllAdaptersFailedError
