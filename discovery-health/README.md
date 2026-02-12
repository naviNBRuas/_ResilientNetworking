# Discovery Health

A robust, thread-safe, in-memory service discovery and health checking library for Python.

## Features

- **Service Registration:** Register service endpoints with metadata.
- **Health Monitoring:**
    - **Active Checks:** Periodically poll services to verify health.
    - **Passive Checks:** Update health status based on interaction results (e.g., failed HTTP requests).
- **Advanced Resolution:**
    - **Metadata Filtering:** Resolve endpoints based on custom tags (e.g., `region`, `env`).
    - **TTL Expiration:** Automatically expire stale endpoints that haven't checked in.
- **Thread-Safety:** Fully thread-safe registry operations.

## Installation

```bash
pip install discovery-health
```

## Usage

### Basic Registration and Resolution

```python
from discovery_health import ServiceRegistry, ServiceEndpoint

registry = ServiceRegistry()

# Register a service
endpoint = ServiceEndpoint(
    address="192.168.1.10:8080",
    metadata={"version": "1.0", "env": "prod"}
)
registry.register("my-service", endpoint)

# Resolve healthy endpoints
endpoints = registry.resolve("my-service")
for ep in endpoints:
    print(f"Found: {ep.address}")
```

### Health Checks

**Active Check:**

```python
def health_checker(ep: ServiceEndpoint) -> bool:
    # Perform actual network call here
    return True

registry.active_check("my-service", health_checker)
```

**Passive Mark:**

```python
# Mark as unhealthy after a failed request
registry.passive_mark("my-service", "192.168.1.10:8080", success=False)
```

### Advanced Features

**TTL (Time-To-Live):**

Services can be registered with a TTL. If they are not checked (active or passive) within the TTL window, they are considered expired.

```python
# Endpoint expires after 5 seconds if not checked
ep = ServiceEndpoint(address="10.0.0.1", ttl=5.0)
registry.register("temp-service", ep)
```

**Metadata Filtering:**

Filter endpoints during resolution.

```python
# Get only 'prod' endpoints in 'us-east'
targets = registry.resolve(
    "my-service",
    filter_metadata={"env": "prod", "region": "us-east"}
)
```

**Pruning Stale Endpoints:**

Remove expired endpoints from the registry to free up memory.

```python
registry.prune()
```

## API Reference

### `ServiceEndpoint`
- `address`: Connection string/URI.
- `metadata`: Dictionary of tags.
- `healthy`: Boolean status.
- `ttl`: Time-to-live in seconds (0.0 = infinite).

### `ServiceRegistry`
- `register(name, endpoint)`
- `unregister(name, address)`
- `resolve(name, filter_metadata=None)`
- `active_check(name, checker_func)`
- `passive_mark(name, address, success)`
- `prune(name=None)`

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=discovery-health
```

## Usage

```python
import discovery_health
```

## Configuration

Discovery health behavior is configured programmatically via `ServiceRegistry`
and `ServiceEndpoint` settings (TTL, metadata, and check callbacks).

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
