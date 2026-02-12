# connection-multiplexer

Resilient connection management layer that multiplexes logical channels over unstable physical links, with pooling, health monitoring, and graceful degradation. Intended to be consumed as a library or service module by downstream systems that require reliable delivery across transports.

## Scope
- Connection pooling, reuse, and prioritization across multiple transports (e.g., TCP, QUIC, WebSockets, custom links).
- Health checks, heartbeats, and fast failover to alternate links.
- Backpressure signaling and flow control hooks for upper layers.
- Pluggable authentication/authorization and encryption boundaries (design-time interfaces, not hardwired deps).

## Deliverables (incremental)
- Core interface definitions (types/IDL) for connection lifecycle and channel multiplexing.
- Reference runtime with policy-driven routing and link selection.
- Test harness with simulated flake/latency/loss scenarios.
- Observability hooks (metrics/events) for connection state transitions.

## Consumption
- **Library:** Import the module and implement the connection adapters for your transports.
- **Service component:** Run the multiplexer as a sidecar/daemon and communicate via defined RPC/IPC APIs.
- Contracts and code are versioned with tags like `connection-multiplexer/v0.1.0`; consumers should pin explicitly.

## Getting Started

### Installation
Clone the repository and install:
```bash
pip install .
```

### Usage
Here is a basic example using `LogTransport` and the observability hooks:

```python
import logging
from connection_multiplexer import ConnectionMultiplexer
from connection_multiplexer.transports import LogTransport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Define an observability callback
def monitor(event: str, data: dict):
    print(f"Monitor: {event} -> {data}")

# Initialize Multiplexer
mux = ConnectionMultiplexer(on_event=monitor)

# Register Transports
# 'primary' has higher priority (lower value)
mux.register("primary", LogTransport("primary", logger), priority=10)
# 'backup' is used if primary fails
mux.register("backup", LogTransport("backup", logger), priority=20)

# Send Data
try:
    response = mux.send({"command": "PING"})
    print("Result:", response)
except Exception as e:
    print("Send failed:", e)

# Cleanup
mux.close()
```

### Key Concepts
- **Priority**: Lower numbers are tried first.
- **Weight**: Used to load balance between transports of the same priority.
- **Observability**: Pass an `on_event` callback to track internal state changes and errors.

## Status
Stable release (v0.1.0).
- Fully implemented connection pooling and prioritization.
- Thread-safe architecture.
- Observability hooks and robust error handling.

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=connection-multiplexer
```

## Usage

```python
import connection_multiplexer
```

## Configuration

Connection multiplexer configuration is set programmatically via transport
registration, priorities, and optional observability callbacks.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.