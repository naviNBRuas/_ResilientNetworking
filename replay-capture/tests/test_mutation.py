
import pytest
from typing import Any, Dict
from replay_capture import InMemoryCaptureStore, Capture, Replayer

def test_handler_mutation_safety():
    store = InMemoryCaptureStore()
    original_req = {"a": 1, "nested": {"b": 2}}
    store.save(Capture(request=original_req, response={}))
    
    def mutation_handler(req: Dict[str, Any]) -> Dict[str, Any]:
        req["a"] = 999
        req["nested"]["b"] = 888
        return {}

    replayer = Replayer(store)
    replayer.replay(mutation_handler)
    
    # Check if store was mutated
    stored_capture = store.list()[0]
    
    # These assertions will likely fail if we don't copy
    assert stored_capture.request["a"] == 1
    assert stored_capture.request["nested"]["b"] == 2
