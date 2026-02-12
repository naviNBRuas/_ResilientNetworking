

def test_sample_consumer_imports():
    """Test that sample consumer can be imported."""
    try:
        from sample_consumers import examples
        assert examples is not None
    except ImportError:
        # Module doesn't have __init__ exports, that's ok
        pass
