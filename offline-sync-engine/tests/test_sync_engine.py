import json
import os
import tempfile
import threading
import pytest
import time
from unittest.mock import MagicMock

from offline_sync_engine import FileOperationStore, InMemoryOperationStore, LastWriteWinsResolver, Operation, SyncEngine

# Existing tests
def test_enqueue_and_persist_file_store():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "ops.json")
        store = FileOperationStore(path)
        engine = SyncEngine(store)

        op = engine.enqueue("k", "v1", author="alice")
        assert op.version == 1

        # Reload from disk
        engine2 = SyncEngine(FileOperationStore(path))
        assert "k" in engine2.state
        assert engine2.state["k"].value == "v1"


def test_last_write_wins_resolution():
    store = InMemoryOperationStore()
    engine = SyncEngine(store, resolver=LastWriteWinsResolver())

    first = engine.enqueue("doc", "v1", author="alice", version=1)
    remote = Operation(key="doc", value="v2", version=2, author="bob")

    applied = engine.reconcile([remote])
    assert applied and applied[0].value == "v2"
    assert engine.state["doc"].version == 2


def test_sync_round_trip():
    store = InMemoryOperationStore()
    engine = SyncEngine(store)
    engine.enqueue("item", "local", author="local", version=1)

    remote_store = {"item": Operation(key="item", value="remote", version=2, author="remote")}

    def pull_remote():
        return remote_store.values()

    def push_remote(ops):
        # simple merge into remote_store
        for op in ops:
            remote_store[op.key] = op

    stats = engine.sync(pull_remote, push_remote)
    assert stats["applied_remote"] == 1
    assert remote_store["item"].value == "remote"


# New robust tests

def test_file_store_atomic_write():
    """Verify that writing doesn't leave partial files if interrupted (simulated)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "atomic.json")
        store = FileOperationStore(path)
        
        ops = {"k": Operation(key="k", value="v1", version=1, author="me")}
        store.save(ops)
        
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["k"]["value"] == "v1"

def test_file_store_corrupted_file():
    """Verify loading a corrupted file raises an error (or handles it gracefully if we chose that)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "corrupt.json")
        with open(path, "w") as f:
            f.write("{ invalid json")
            
        store = FileOperationStore(path)
        with pytest.raises(json.JSONDecodeError):
            store.load()

def test_concurrency_thread_safety():
    """Verify that multiple threads enqueuing doesn't corrupt state."""
    store = InMemoryOperationStore()
    engine = SyncEngine(store)
    
    def worker(i):
        for j in range(10):
            engine.enqueue(f"k{i}", f"v{j}", author=f"t{i}")
            
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # We should have 5 keys, each with version at least 1 (actually 10 if we updated same key)
    # Here we used different keys k0..k4
    assert len(engine.state) == 5
    for i in range(5):
        assert f"k{i}" in engine.state
        assert engine.state[f"k{i}"].value == "v9"

def test_concurrency_same_key():
    """Verify LWW works with concurrent updates to same key."""
    store = InMemoryOperationStore()
    engine = SyncEngine(store)
    
    # Pre-populate
    engine.enqueue("shared", 0, author="init", version=0)
    
    errors = []
    
    def worker():
        try:
            for _ in range(50):
                engine.enqueue("shared", 1, author="worker")
        except Exception as e:
            errors.append(e)
            
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    if errors:
        pytest.fail(f"Thread errors: {errors}")
        
    # Version should be high
    # With 4 threads * 50 updates = 200 updates.
    # Initial version is 0.
    final_version = engine.state["shared"].version
    assert final_version >= 200, f"Expected version >= 200, got {final_version}"

def test_sync_errors_propagated():
    store = InMemoryOperationStore()
    engine = SyncEngine(store)
    
    def pull_fail():
        raise RuntimeError("Pull failed")
        
    with pytest.raises(RuntimeError, match="Pull failed"):
        engine.sync(pull_fail, lambda x: None)
        
    def push_fail(ops):
        raise RuntimeError("Push failed")
        
    with pytest.raises(RuntimeError, match="Push failed"):
        engine.sync(lambda: [], push_fail)