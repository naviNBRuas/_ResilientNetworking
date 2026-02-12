# Session Continuity

A robust, thread-safe Python library for managing user sessions and idempotency keys. This module provides in-memory storage for session management and idempotency caching, suitable for transient state management in distributed systems or lightweight applications.

## Features

- **Session Management**: Create, resume, and expire user sessions with metadata support.
- **Idempotency Cache**: Store and retrieve idempotency keys to prevent duplicate operations.
- **Thread Safety**: Fully thread-safe implementations using `RLock`.
- **TTL Support**: Automatic expiration of sessions and cache entries.
- **Logging**: Integrated logging for better observability.
- **Type Hinted**: Fully typed for better developer experience and tooling support.

## Installation

This package is intended to be installed as part of the Resilient Networking project or as a standalone dependency.

```bash
pip install .
```

## Usage

### Session Manager

Manage user sessions with `SessionManager`.

```python
import time
from session_continuity import SessionManager

# Initialize with a 1-hour TTL
manager = SessionManager(ttl_seconds=3600)

# Create a new session with metadata
session = manager.create(metadata={"user_id": 123, "role": "admin"})
print(f"Session ID: {session.session_id}")
print(f"Resume Token: {session.resume_token}")

# Resume a session
resumed_session = manager.resume(session.resume_token)
if resumed_session:
    print(f"Resumed session for user: {resumed_session.metadata['user_id']}")
else:
    print("Session expired or invalid token.")

# Touch a session to extend its life
manager.touch(session.session_id)

# Cleanup expired sessions (e.g., in a background task)
expired_count = manager.reap_expired()
print(f"Cleaned up {expired_count} expired sessions.")
```

### Idempotency Cache

Prevent duplicate operations with `IdempotencyCache`.

```python
from session_continuity import IdempotencyCache

# Initialize with a 10-minute TTL
cache = IdempotencyCache(ttl_seconds=600)

request_id = "req-unique-123"
response_data = {"status": "success", "order_id": 456}

# Store the result
cache.remember(request_id, response_data)

# Retrieve the result later
cached_response = cache.get(request_id)
if cached_response:
    print("Returned cached response")
else:
    print("Processing new request...")
```

## Development

1.  **Install dependencies**:
    ```bash
    pip install -e .[dev]
    ```

2.  **Run tests**:
    ```bash
    pytest tests/
    ```

## License

MIT

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=session-continuity
```

## Usage

```python
import session_continuity
```

## Configuration

Session behavior is configured via `SessionManager` and `IdempotencyCache`
constructor options (TTL, logging, and storage settings).

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
