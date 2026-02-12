# Congestion Control

A robust, thread-safe Python library for adaptive rate limiting and congestion control. This package provides a token bucket implementation and an adaptive controller that adjusts rates based on latency feedback (AIMD strategy).

## Features

- **TokenBucket**: 
  - Precise rate limiting using `time.monotonic`.
  - Thread-safe implementation.
  - Support for burst capacity.
  
- **AdaptiveCongestionController**:
  - Automatically adjusts flow rate based on network feedback.
  - Implements Additive Increase / Multiplicative Decrease (AIMD).
  - Configurable latency thresholds for stabilization.

## Installation

Requires Python 3.10+.

```bash
pip install congestion-control
```

## Usage

### Basic Token Bucket

```python
from congestion_control import TokenBucket
import time

# Create a bucket with 10 tokens/sec rate and 20 burst capacity
bucket = TokenBucket(rate=10.0, capacity=20.0)

# Consume tokens
if bucket.allow(cost=1.0):
    print("Request allowed")
else:
    print("Rate limit exceeded")
```

### Adaptive Control

```python
from congestion_control import AdaptiveCongestionController, TokenBucket

bucket = TokenBucket(rate=10.0, capacity=20.0)
controller = AdaptiveCongestionController(
    bucket,
    min_rate=5.0,
    max_rate=100.0,
    high_latency_threshold=500.0 # ms
)

# Simulate feedback loop
try:
    start = time.monotonic()
    # ... perform network request ...
    latency_ms = (time.monotonic() - start) * 1000
    
    # Update controller based on success/latency
    controller.on_success(rtt_ms=latency_ms)
    
except Exception:
    # Scale back on errors
    controller.on_congestion_signal()
```

## Development

1. **Install dependencies**:
   ```bash
   pip install -e .[dev]
   ```

2. **Run tests**:
   ```bash
   pytest
   ```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=congestion-control
```

## Usage

```python
import congestion_control
```

## Configuration

Configure token bucket and AIMD parameters via `TokenBucket` and
`AdaptiveCongestionController` constructor options.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
