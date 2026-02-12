
import pytest
from replay_capture import InMemoryCaptureStore, Capture, Replayer

def test_stop_on_failure_mismatch():
    store = InMemoryCaptureStore()
    store.save(Capture(request={"id": 1}, response={"val": 1}))
    store.save(Capture(request={"id": 2}, response={"val": 2}))
    store.save(Capture(request={"id": 3}, response={"val": 3}))

    # Handler fails on id=2
    def handler(req):
        if req["id"] == 2:
            return {"val": 999}
        return {"val": req["id"]}

    replayer = Replayer(store)
    result = replayer.replay(handler, stop_on_failure=True)

    assert result.successes == 1
    assert result.failure_count == 1
    assert len(result.failures) == 1
    assert result.failures[0].capture.request["id"] == 2
    # Should not have run id=3 (total runs = 1 success + 1 failure = 2)
    assert result.total_runs == 2

def test_stop_on_failure_error():
    store = InMemoryCaptureStore()
    store.save(Capture(request={"id": 1}, response={"val": 1}))
    store.save(Capture(request={"id": 2}, response={"val": 2}))
    store.save(Capture(request={"id": 3}, response={"val": 3}))

    # Handler raises on id=2
    def handler(req):
        if req["id"] == 2:
            raise ValueError("Stop here")
        return {"val": req["id"]}

    replayer = Replayer(store)
    result = replayer.replay(handler, stop_on_failure=True)

    assert result.successes == 1
    assert result.failure_count == 1
    assert str(result.failures[0].error) == "Stop here"
    assert result.total_runs == 2

def test_continue_on_failure():
    store = InMemoryCaptureStore()
    store.save(Capture(request={"id": 1}, response={"val": 1}))
    store.save(Capture(request={"id": 2}, response={"val": 2})) # Will fail
    store.save(Capture(request={"id": 3}, response={"val": 3}))

    def handler(req):
        if req["id"] == 2:
            return {"val": 999}
        return {"val": req["id"]}

    replayer = Replayer(store)
    result = replayer.replay(handler, stop_on_failure=False)

    assert result.successes == 2
    assert result.failure_count == 1
    assert result.total_runs == 3
