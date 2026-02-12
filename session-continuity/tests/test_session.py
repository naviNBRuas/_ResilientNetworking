import time
import threading
from session_continuity import IdempotencyCache, SessionManager

def test_session_create_and_resume():
    mgr = SessionManager(ttl_seconds=1)
    state = mgr.create({"user": "alice"})
    assert state.session_id is not None
    assert state.resume_token is not None
    assert state.metadata == {"user": "alice"}
    
    resumed = mgr.resume(state.resume_token)
    assert resumed is not None
    assert resumed.session_id == state.session_id
    assert resumed.metadata == {"user": "alice"}

def test_session_resume_invalid_token():
    mgr = SessionManager(ttl_seconds=1)
    mgr.create()
    assert mgr.resume("invalid-token") is None

def test_session_expiry():
    mgr = SessionManager(ttl_seconds=0.1)
    state = mgr.create()
    time.sleep(0.15)
    # Should not be resumable even before reap
    assert mgr.resume(state.resume_token) is None
    
    expired = mgr.reap_expired()
    assert expired == 1
    assert mgr.get_session(state.session_id) is None

def test_session_touch():
    mgr = SessionManager(ttl_seconds=0.2)
    state = mgr.create()
    time.sleep(0.1)
    mgr.touch(state.session_id)
    time.sleep(0.15)
    # Total time 0.25s, but touched at 0.1s, so should be valid (0.15s since last seen < 0.2s)
    # Wait, 0.1s elapsed, touched. Then 0.15s elapsed. Total since touch = 0.15s. TTL = 0.2s.
    # Should be valid.
    assert mgr.resume(state.resume_token) is not None

def test_idempotency_cache():
    cache = IdempotencyCache(ttl_seconds=0.1)
    cache.remember("k", "v")
    assert cache.get("k") == "v"
    time.sleep(0.15)
    assert cache.get("k") is None

def test_idempotency_overwrite():
    cache = IdempotencyCache(ttl_seconds=1)
    cache.remember("k", "v1")
    assert cache.get("k") == "v1"
    cache.remember("k", "v2")
    assert cache.get("k") == "v2"

def test_session_concurrency():
    mgr = SessionManager(ttl_seconds=5)
    
    def worker():
        for _ in range(100):
            mgr.create({"data": "test"})
            
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # We can't easily assert exact count due to internal implementation details (reap might not happen)
    # But we can check consistency.
    assert len(mgr._sessions) == 1000

def test_idempotency_concurrency():
    cache = IdempotencyCache(ttl_seconds=5)
    
    def worker(i):
        for j in range(100):
            cache.remember(f"k-{i}-{j}", f"v-{i}-{j}")
            
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert len(cache._cache) == 1000
    for i in range(10):
        for j in range(100):
            assert cache.get(f"k-{i}-{j}") == f"v-{i}-{j}"

def test_cleanup_logic():
    cache = IdempotencyCache(ttl_seconds=0.1)
    cache.remember("k1", "v1")
    time.sleep(0.05)
    cache.remember("k2", "v2")
    time.sleep(0.1) 
    # k1 (0.15s old) should be expired, k2 (0.1s old) might be expired if exactly equal, but usually > ttl.
    # Let's sleep a bit more to be sure about k1 and less for k2? 
    # Better:
    # T=0: k1
    # T=0.15: k1 is > 0.1 old. k2 create.
    # T=0.20: k2 is 0.05 old.
    
    cache = IdempotencyCache(ttl_seconds=0.2)
    cache.remember("expired", "v")
    time.sleep(0.3)
    cache.remember("fresh", "v")
    
    removed = cache.cleanup()
    assert removed >= 1
    assert cache.get("expired") is None
    assert cache.get("fresh") == "v"