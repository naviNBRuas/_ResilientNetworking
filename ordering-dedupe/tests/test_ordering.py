import threading
import time
from ordering_dedupe import Deduplicator, Sequencer
from ordering_dedupe.sequencer import Reorderer


def test_sequencer_basic():
    seq = Sequencer()
    assert seq.issue() == 1
    assert seq.issue() == 2
    assert seq.issue() == 3


def test_sequencer_reorder_static():
    # Test the static utility
    items = [(2, "b"), (1, "a"), (3, "c")]
    ordered = Sequencer.reorder(items)
    assert ordered == ["a", "b", "c"]


def test_deduplicator_ttl():
    d = Deduplicator(ttl_seconds=0.1)
    assert d.seen("k") is False  # New
    assert d.seen("k") is True   # Seen
    time.sleep(0.15)
    assert d.seen("k") is False  # Expired


def test_deduplicator_max_count():
    # Create small deduplicator
    d = Deduplicator(ttl_seconds=60, max_count=5)
    
    # Fill it
    for i in range(5):
        assert d.seen(f"k{i}") is False
        
    assert len(d._seen) == 5
    
    # Add one more
    assert d.seen("k5") is False
    # Should still be 5 (one evicted)
    assert len(d._seen) == 5
    
    # Check that older keys are gone or at least size is maintained
    # Note: Exact eviction policy depends on implementation details, 
    # but size constraint is the contract.
    assert len(d._seen) <= 5


def test_reorderer_in_order():
    r = Reorderer()
    assert r.push(1, "a") == ["a"]
    assert r.push(2, "b") == ["b"]
    assert r.push(3, "c") == ["c"]


def test_reorderer_out_of_order():
    r = Reorderer()
    # Receive 3, then 1, then 2
    assert r.push(3, "c") == []
    assert r.push(1, "a") == ["a"]
    # 2 arrives, filling the gap for 2 and 3
    assert r.push(2, "b") == ["b", "c"]


def test_reorderer_duplicates_and_late():
    r = Reorderer()
    r.push(1, "a")
    
    # Duplicate 1
    assert r.push(1, "a") == []
    
    # Late 0
    assert r.push(0, "late") == []


def test_reorderer_gap():
    r = Reorderer()
    r.push(1, "a")
    r.push(3, "c")
    r.push(4, "d")
    # Waiting for 2...
    assert r.next_expected == 2
    
    # 2 arrives
    result = r.push(2, "b")
    assert result == ["b", "c", "d"]
    assert r.next_expected == 5


def test_concurrency_sequencer():
    seq = Sequencer()
    
    def worker():
        for _ in range(100):
            seq.issue()
            
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # 10 threads * 100 issues = 1000 items issued
    # Next should be 1001
    assert seq.next_seq == 1001


def test_concurrency_deduplicator():
    d = Deduplicator(ttl_seconds=10, max_count=1000)
    
    def worker():
        for i in range(100):
            d.seen(f"key-{threading.get_ident()}-{i}")
            
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert len(d._seen) == 1000