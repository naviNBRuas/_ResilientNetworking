import threading
import time
import random
from connection_multiplexer import ConnectionMultiplexer, SimulatedTransport

def test_concurrent_sends():
    """Test multiple threads sending simultaneously."""
    mux = ConnectionMultiplexer()
    # Add multiple transports
    for i in range(5):
        mux.register(f"t{i}", SimulatedTransport(f"t{i}", base_latency_ms=10, jitter_ms=5))

    success_count = 0
    errors = []
    lock = threading.Lock()

    def worker():
        nonlocal success_count
        try:
            for _ in range(10):
                mux.send({"data": "payload"})
                with lock:
                    success_count += 1
        except Exception as e:
            with lock:
                errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors occurred: {errors}"
    assert success_count == 100

def test_concurrent_register_send():
    """Test registering/unregistering while sending."""
    mux = ConnectionMultiplexer()
    mux.register("stable", SimulatedTransport("stable", base_latency_ms=1))

    stop_event = threading.Event()
    errors = []

    def sender():
        try:
            while not stop_event.is_set():
                mux.send("data")
                time.sleep(0.001)
        except Exception as e:
            errors.append(e)

    def toggler():
        try:
            while not stop_event.is_set():
                name = "dynamic"
                # Register
                t = SimulatedTransport(name)
                mux.register(name, t)
                time.sleep(0.002)
                # Unregister
                mux.unregister(name)
                time.sleep(0.002)
        except Exception as e:
            errors.append(e)

    t_sender = threading.Thread(target=sender)
    t_toggler = threading.Thread(target=toggler)

    t_sender.start()
    t_toggler.start()

    time.sleep(1)
    stop_event.set()
    t_sender.join()
    t_toggler.join()

    assert not errors, f"Errors occurred: {errors}"
