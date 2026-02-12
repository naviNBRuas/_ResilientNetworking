import json
from pathlib import Path
from typing import Any, Dict

import pytest
from replay_capture import (
    Capture,
    InMemoryCaptureStore,
    JSONFileCaptureStore,
    Replayer,
    ReplayFailure,
)


def test_replay_matches_handler():
    store = InMemoryCaptureStore()
    store.save(Capture(request={"x": 1}, response={"y": 2}))

    def handler(req: Dict[str, Any]) -> Dict[str, Any]:
        return {"y": req["x"] + 1}

    result = Replayer(store).replay(handler)
    assert result.successes == 1
    assert result.failure_count == 0
    assert result.total_runs == 1


def test_replay_mismatch_counts_failure():
    store = InMemoryCaptureStore()
    store.save(Capture(request={"x": 1}, response={"y": 3}))  # Expect 3

    def handler(req: Dict[str, Any]) -> Dict[str, Any]:
        return {"y": req["x"] + 1}  # Returns 2

    result = Replayer(store).replay(handler)
    assert result.successes == 0
    assert result.failure_count == 1
    assert len(result.failures) == 1
    
    failure = result.failures[0]
    assert failure.actual_response == {"y": 2}
    assert failure.error is None
    assert "Mismatch" in str(failure)


def test_replay_exception_handling():
    store = InMemoryCaptureStore()
    store.save(Capture(request={"x": 1}, response={"y": 2}))

    def handler(req: Dict[str, Any]) -> Dict[str, Any]:
        raise ValueError("Boom")

    result = Replayer(store).replay(handler)
    assert result.successes == 0
    assert result.failure_count == 1
    
    failure = result.failures[0]
    assert isinstance(failure.error, ValueError)
    assert str(failure.error) == "Boom"
    assert "Error" in str(failure)


def test_json_file_store(tmp_path: Path):
    fpath = tmp_path / "captures.jsonl"
    store = JSONFileCaptureStore(fpath)
    
    cap1 = Capture(request={"a": 1}, response={"b": 2})
    cap2 = Capture(request={"a": 10}, response={"b": 20})
    
    store.save(cap1)
    store.save(cap2)
    
    # Verify file content
    lines = fpath.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"request": {"a": 1}, "response": {"b": 2}}
    
    # Verify list()
    # Create new store instance to test reading
    store2 = JSONFileCaptureStore(fpath)
    loaded = store2.list()
    assert len(loaded) == 2
    assert loaded[0] == cap1
    assert loaded[1] == cap2


def test_json_file_store_empty(tmp_path: Path):
    fpath = tmp_path / "empty.jsonl"
    store = JSONFileCaptureStore(fpath)
    assert store.list() == []