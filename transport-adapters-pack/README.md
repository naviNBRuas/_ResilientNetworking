# Transport Adapters Pack

A collection of pluggable transport adapters for various network protocols (HTTP, WebSocket, MQTT).

## Overview

This package provides a unified `TransportAdapter` interface for sending data over different transport layers. It includes:
- **HTTP Adapter**: A fully functional, standard-library based (urllib) HTTP client.
- **MQTT Stub**: A simulation adapter for MQTT (useful for testing without a broker).
- **WebSocket Stub**: A simulation adapter for WebSockets.

## Installation

```bash
pip install transport-adapters-pack
```

## Usage

### HTTP Adapter

The HTTP adapter uses Python's standard `urllib` to make real network requests. It supports JSON encoding/decoding and query parameters.

```python
import logging
from transport_adapters_pack import HttpAdapter, TransportError

# Configure logging to see adapter activity
logging.basicConfig(level=logging.DEBUG)

# Initialize with an optional base URL
adapter = HttpAdapter(base_url="https://httpbin.org")

try:
    # Send a request
    response = adapter.send({
        "path": "/post",
        "method": "POST",
        "params": {"id": 123},       # Query parameters
        "body": {"key": "value"}     # Automatically JSON-encoded
    })
    
    print(f"Status: {response.status}")
    print(f"Body: {response.body}")
    
except TransportError as e:
    print(f"Request failed: {e}")
```

### MQTT Stub

The MQTT stub simulates publishing messages and logs the activity.

```python
from transport_adapters_pack import MqttStubAdapter

adapter = MqttStubAdapter()
response = adapter.send({"topic": "sensors/temp", "payload": "23.5"})
print(response.body)
```

## Architecture

All adapters inherit from `TransportAdapter` and implement:
- `supports(capabilities: dict) -> bool`: Checks if the adapter handles the required capabilities.
- `send(request: dict) -> TransportResponse`: Sends a request and returns a response.
- `close()`: Cleans up resources.

## Exceptions

- `TransportError`: Base exception.
- `ConnectionError`: Network connectivity issues.
- `TimeoutError`: Request timed out.
- `ProtocolError`: Invalid usage or protocol violation.

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=transport-adapters-pack
```

## Usage

```python
import transport_adapters_pack
```

## Configuration

Transport adapters are configured via constructor parameters (base URL, timeouts,
and adapter-specific options).

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.