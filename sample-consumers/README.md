# sample-consumers

Example consumer demonstrating composition of:
- `connection-multiplexer` for transport selection
- `adaptive-retry-strategy` for intelligent retries
- `protocol-fallback-layer` for graceful protocol degradation

## Structure
- `src/sample_consumers/examples/client.py` — Resilient client composing the layers. It includes a **Mock Mode** to run standalone if dependencies are missing.
- `src/sample_consumers/examples/server_stub.py` — Stub TCP server to test against.
- `tests/` — Integration tests validating the client logic.

## Usage

### Prerequisites
- Python 3.10+
- Dependencies (optional, for real mode): `connection-multiplexer`, `adaptive-retry-strategy`, `protocol-fallback-layer`

### Installation
```bash
pip install -e .[dev]
```

### Running the Sample Client
You can run the client directly. It will attempt to import the resilience layers. If not found, it uses internal mocks to demonstrate the logic.

```bash
python src/sample_consumers/examples/client.py
```

### Running the Stub Server
To test against a local server (if not using mocks or to test network interaction):
```bash
python src/sample_consumers/examples/server_stub.py
```

### Running Tests
```bash
pytest tests/
```

## Resilience Architecture
The client demonstrates the following composition:
1. **Fallback Layer**: Wraps the operation. If the primary protocol (e.g., TCP) fails, it switches to the fallback (e.g., UDP).
2. **Retry Strategy**: Wraps the network call. Retries transient failures with exponential backoff.
3. **Multiplexer**: Handles the actual transport.

Logic Flow: `Fallback(Retry(Multiplexer))`

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=sample-consumers
```

## Usage

```python
import sample_consumers
```

## Configuration

Sample consumers are configured via the example scripts and their CLI flags.
Mocks can be enabled when dependencies are unavailable.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.