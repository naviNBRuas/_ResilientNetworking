# Replay Capture

Request/response capture and replay utilities for deterministic testing and resilience validation.

## Features

- **Capture stores**: In-memory and JSON Lines file backends.
- **Replay engine**: Re-run captured requests against handlers.
- **Failure reporting**: Detailed replay results and errors.

## Usage

```python
from replay_capture import Capture, InMemoryCaptureStore, Replayer

store = InMemoryCaptureStore()
store.save(Capture(request={"op": "ping"}, response={"status": "ok"}))

replayer = Replayer(store)
result = replayer.replay(lambda req: {"status": "ok"})
print(result.successes)
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=replay-capture
```

## Usage

```python
import replay_capture
```

## Configuration

Configure storage backends via `InMemoryCaptureStore` or `JSONFileCaptureStore`, and
replay behavior via `Replayer` options.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
