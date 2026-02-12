from concurrent.futures import ThreadPoolExecutor
from discovery_health import ServiceEndpoint, ServiceRegistry


def test_register_and_resolve():
    reg = ServiceRegistry()
    reg.register("api", ServiceEndpoint(address="1.2.3.4"))
    
    resolved = reg.resolve("api")
    assert len(resolved) == 1
    assert resolved[0].address == "1.2.3.4"
    assert resolved[0].healthy is True


def test_duplicate_registration():
    reg = ServiceRegistry()
    ep1 = ServiceEndpoint(address="1.2.3.4")
    ep2 = ServiceEndpoint(address="1.2.3.4")  # Same address

    reg.register("api", ep1)
    reg.register("api", ep2)  # Should be ignored

    resolved = reg.resolve("api")
    assert len(resolved) == 1


def test_unregister():
    reg = ServiceRegistry()
    reg.register("api", ServiceEndpoint(address="1.2.3.4"))
    
    assert reg.unregister("api", "1.2.3.4") is True
    assert reg.resolve("api") == []
    
    # Unregistering non-existent
    assert reg.unregister("api", "1.2.3.4") is False
    assert reg.unregister("unknown_service", "1.2.3.4") is False


def test_active_check_and_random():
    reg = ServiceRegistry()
    reg.register("api", ServiceEndpoint(address="good"))
    reg.register("api", ServiceEndpoint(address="bad"))

    def checker(ep):
        return ep.address == "good"

    reg.active_check("api", checker)
    
    # "bad" should be unhealthy now
    resolved = reg.resolve("api")
    assert len(resolved) == 1
    assert resolved[0].address == "good"

    # Random should always pick the healthy one
    for _ in range(5):
        ep = reg.random_endpoint("api")
        assert ep is not None
        assert ep.address == "good"


def test_active_check_error_handling():
    reg = ServiceRegistry()
    reg.register("api", ServiceEndpoint(address="error_prone"))

    def broken_checker(ep):
        raise ValueError("Something went wrong")

    # Should catch the exception and mark as unhealthy
    reg.active_check("api", broken_checker)
    
    resolved = reg.resolve("api")
    assert len(resolved) == 0


def test_passive_mark():
    reg = ServiceRegistry()
    reg.register("svc", ServiceEndpoint(address="a"))
    
    # Mark unhealthy
    reg.passive_mark("svc", "a", success=False)
    assert reg.resolve("svc") == []
    
    # Mark healthy again
    reg.passive_mark("svc", "a", success=True)
    resolved = reg.resolve("svc")
    assert len(resolved) == 1
    assert resolved[0].address == "a"


def test_get_service_names():
    reg = ServiceRegistry()
    reg.register("svc1", ServiceEndpoint(address="a"))
    reg.register("svc2", ServiceEndpoint(address="b"))
    
    names = reg.get_service_names()
    assert len(names) == 2
    assert "svc1" in names
    assert "svc2" in names
    
    # After unregistering all endpoints for a service, it should be removed
    reg.unregister("svc1", "a")
    names = reg.get_service_names()
    assert "svc1" not in names
    assert "svc2" in names


def test_thread_safety_smoke_test():
    """Simple stress test to ensure no exceptions/corruption under load."""
    reg = ServiceRegistry()
    
    def worker(i):
        name = "svc"
        addr = f"addr-{i}"
        reg.register(name, ServiceEndpoint(address=addr))
        # Toggle health
        reg.passive_mark(name, addr, success=False)
        reg.passive_mark(name, addr, success=True)
        # Read
        reg.resolve(name)
        # Unregister half of them
        if i % 2 == 0:
            reg.unregister(name, addr)

    # 100 threads accessing the same registry
    with ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(worker, range(100)))
    
    # Check consistency
    # 50 endpoints should remain
    resolved = reg.resolve("svc")
    assert len(resolved) == 50