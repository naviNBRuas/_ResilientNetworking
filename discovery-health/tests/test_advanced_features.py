import time
from discovery_health import ServiceEndpoint, ServiceRegistry

def test_ttl_expiration():
    reg = ServiceRegistry()
    # TTL of 0.1 seconds
    reg.register("fast-expire", ServiceEndpoint(address="1.1.1.1", ttl=0.1))
    
    # Should be available immediately
    assert len(reg.resolve("fast-expire")) == 1
    
    # Wait for expiration
    time.sleep(0.2)
    
    # Should not be resolved (lazy check)
    assert len(reg.resolve("fast-expire")) == 0
    
    # Prune should report 1 removed
    assert reg.prune("fast-expire") == 1
    
    # Registry should be empty for this service now
    assert len(reg.resolve("fast-expire")) == 0
    # And specifically, the service key should be gone if it was the only endpoint
    assert "fast-expire" not in reg.get_service_names()


def test_metadata_filtering():
    reg = ServiceRegistry()
    ep1 = ServiceEndpoint(address="us-1", metadata={"region": "us-east", "env": "prod"})
    ep2 = ServiceEndpoint(address="eu-1", metadata={"region": "eu-west", "env": "prod"})
    ep3 = ServiceEndpoint(address="us-2", metadata={"region": "us-east", "env": "dev"})
    
    reg.register("api", ep1)
    reg.register("api", ep2)
    reg.register("api", ep3)
    
    # No filter
    assert len(reg.resolve("api")) == 3
    
    # Filter by region
    us_eps = reg.resolve("api", filter_metadata={"region": "us-east"})
    assert len(us_eps) == 2
    assert {ep.address for ep in us_eps} == {"us-1", "us-2"}
    
    # Filter by multiple
    prod_us = reg.resolve("api", filter_metadata={"region": "us-east", "env": "prod"})
    assert len(prod_us) == 1
    assert prod_us[0].address == "us-1"
    
    # Filter no match
    assert len(reg.resolve("api", filter_metadata={"region": "asia"})) == 0


def test_active_check_resets_ttl():
    reg = ServiceRegistry()
    # TTL 0.5s
    reg.register("keepalive", ServiceEndpoint(address="alive", ttl=0.5))
    
    time.sleep(0.3)
    # Still valid
    assert len(reg.resolve("keepalive")) == 1
    
    # Update via active check
    def checker(ep):
        return True
    
    reg.active_check("keepalive", checker)
    
    # Wait another 0.3s (total 0.6s since start, but only 0.3s since check)
    time.sleep(0.3)
    
    # Should still be valid because last_checked was updated
    assert len(reg.resolve("keepalive")) == 1
    
    # Wait until it expires
    time.sleep(0.3)
    assert len(reg.resolve("keepalive")) == 0
