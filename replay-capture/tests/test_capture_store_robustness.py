
import json
import pytest
from replay_capture.capture import JSONFileCaptureStore, CaptureReadError

def test_json_store_corrupt_line(tmp_path):
    fpath = tmp_path / "corrupt.jsonl"
    fpath.write_text('{"request": {}, "response": {}}\nINVALID\n{"request": {"a": 1}, "response": {"b": 2}}', encoding="utf-8")
    
    store = JSONFileCaptureStore(fpath)
    
    with pytest.raises(CaptureReadError) as exc:
        store.list()
    
    assert "Failed to decode JSON at line 2" in str(exc.value)

def test_json_store_missing_fields(tmp_path):
    fpath = tmp_path / "incomplete.jsonl"
    # Second line missing 'response'
    fpath.write_text('{"request": {}, "response": {}}\n{"request": {}}', encoding="utf-8")
    
    store = JSONFileCaptureStore(fpath)
    
    with pytest.raises(CaptureReadError) as exc:
        store.list()
        
    assert "Missing required field at line 2" in str(exc.value)

