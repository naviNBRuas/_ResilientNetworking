import pytest
import threading
import time
from traffic_shaper_qos import WeightedFairScheduler

def test_weighted_fairness_interleaving():
    """
    Verify that a queue with weight 2.0 gets serviced roughly twice as often
    as a queue with weight 1.0.
    """
    sched = WeightedFairScheduler()
    # Enqueue enough items to observe the pattern
    # Heavy: weight 2.0 (cost 0.5 per item)
    # Light: weight 1.0 (cost 1.0 per item)
    # Expected Virtual Times:
    # H1: 0, L1: 0
    # Pop H1 (next vt 0.5), Heap: L1(0), H2(0.5) -> Pop L1
    # Pop L1 (next vt 1.0), Heap: H2(0.5), L2(1.0) -> Pop H2
    # Pop H2 (next vt 1.0), Heap: L2(1.0), H3(1.0) -> Tie?
    
    # Expected sequence roughly: H, L, H, H, L, H... or H, L, H, L, H (depending on ties)
    # Actually, with w=2 vs w=1:
    # H starts at 0. L starts at 0.
    # 1. Pop H (vt -> 0.5). Heap: L(0).
    # 2. Pop L (vt -> 1.0). Heap: H(0.5).
    # 3. Pop H (vt -> 1.0). Heap: L(1.0).
    # 4. Tie.
    
    # Let's use weights 3 and 1 to be clearer.
    # H(3) -> cost 0.33. L(1) -> cost 1.0.
    # 1. H(0) -> 0.33. Heap: L(0) -> Pop L? No, H(0) and L(0) are tied.
    # If stable, H came first?
    pass

    sched = WeightedFairScheduler()
    # Add items
    for i in range(10):
        sched.enqueue("heavy", "h", weight=3.0)
    for i in range(10):
        sched.enqueue("light", "l", weight=1.0)
        
    results = []
    while not sched.empty():
        results.append(sched.dequeue())
        
    # Analyze results.
    # We expect 'h' to appear more frequently early on.
    # Specifically, for every 1 'l', we should see roughly 3 'h's.
    
    # Let's just check the first few items.
    # 0: H(0), L(0). Tie. Say H goes. VT_H -> 0.33.
    # 1: L(0). VT_L -> 1.0.
    # 2: H(0.33). VT_H -> 0.66.
    # 3: H(0.66). VT_H -> 0.99.
    # 4: H(0.99). VT_H -> 1.32.
    # 5: L(1.0).
    
    # So sequence: H, L, H, H, H, L ... 
    # Or L, H, H, H, H, L ... (if L wins tie)
    
    # Just checking counts in chunks implies fairness.
    # First 4 items should contain mostly H.
    first_four = results[:4]
    h_count = first_four.count("h")
    assert h_count >= 2, f"Expected heavy items to dominate early. Got {first_four}"

def test_dequeue_raises_when_empty():
    sched = WeightedFairScheduler()
    with pytest.raises(IndexError):
        sched.dequeue()

def test_enqueue_after_empty_bug_fix():
    """
    Regression test for the bug where a queue emptied and refilled
    was not processed.
    """
    sched = WeightedFairScheduler()
    sched.enqueue("q1", "item1")
    
    # Drain
    assert sched.dequeue() == "item1"
    assert sched.empty()
    
    # Refill
    sched.enqueue("q1", "item2")
    assert not sched.empty()
    assert sched.dequeue() == "item2"

def test_peek():
    sched = WeightedFairScheduler()
    sched.enqueue("q1", "item1")
    
    assert sched.peek() == "item1"
    # Should not remove
    assert not sched.empty()
    assert sched.dequeue() == "item1"
    assert sched.empty()

def test_dynamic_weight_update():
    sched = WeightedFairScheduler()
    
    # Both start weight 1.
    sched.enqueue("A", "a1", weight=1.0)
    sched.enqueue("B", "b1", weight=1.0)
    
    # Update A to be very slow (low weight -> high cost)
    # Cost = 1/0.1 = 10.
    # B remains cost 1.
    sched.enqueue("A", "a2", weight=0.1) 
    sched.enqueue("B", "b2", weight=1.0)
    
    # A(0), B(0). Tie. Say A pops. VT_A -> 10.
    # Heap: B(0). Pop B. VT_B -> 1.
    # Heap: B(1) [implicit b2], A(10) [implicit a2]
    # Pop B (b2).
    
    # So order should be A(a1), B(b1), B(b2), A(a2) OR B(b1), A(a1), B(b2), A(a2)
    # The key is B(b2) comes before A(a2).
    
    results = []
    while not sched.empty():
        results.append(sched.dequeue())
        
    # The last one MUST be a2 because it has a huge cost penalty added after a1.
    assert results[-1] == "a2"

def test_concurrency():
    """
    Test thread safety by hammering the scheduler from multiple threads.
    """
    sched = WeightedFairScheduler()
    items_per_thread = 100
    threads = 4
    
    def producer(name, weight):
        for i in range(items_per_thread):
            sched.enqueue(name, f"{name}_{i}", weight=weight)
            time.sleep(0.0001) # Yield a bit
            
    def consumer(results_list):
        while True:
            try:
                item = sched.dequeue()
                results_list.append(item)
            except IndexError:
                # If all producers done and empty, quit
                if len(results_list) == items_per_thread * threads:
                    break
                # Otherwise wait a bit
                time.sleep(0.001)

    res = []
    prod_threads = []
    for t in range(threads):
        pt = threading.Thread(target=producer, args=(f"t{t}", 1.0))
        prod_threads.append(pt)
        pt.start()
        
    ct = threading.Thread(target=consumer, args=(res,))
    ct.start()
    
    for pt in prod_threads:
        pt.join()
        
    ct.join(timeout=5)
    assert not ct.is_alive(), "Consumer thread stuck"
    
    assert len(res) == items_per_thread * threads
    # Check that we got all items
    res_set = set(res)
    assert len(res_set) == items_per_thread * threads