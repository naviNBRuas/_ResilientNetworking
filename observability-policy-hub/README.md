# Observability Policy Hub

A lightweight, thread-safe library for in-memory metrics collection and policy evaluation.

## Features

- **Metric Registry**: 
  - Thread-safe counters, gauges, and histograms.
  - Bounded histograms (sliding window) to prevent memory leaks.
  - Summary statistics (count, avg, p50, p95, p99).
- **Policy Engine**:
  - Simple rule-based evaluation.
  - Fail-safe execution (configurable fail-open/fail-closed).
  - Detailed decision reasoning.

## Installation

This is a library module. Ensure it is in your python path or installed via pip if packaged.

## Usage

### Metrics

```python
from observability_policy_hub import MetricRegistry

# Initialize with custom window size for histograms (default 1000)
metrics = MetricRegistry(histogram_window_size=500)

# Record metrics
metrics.inc("requests_total")
metrics.set_gauge("active_users", 42)
metrics.observe("response_time", 0.15)

# Get summary
summary = metrics.summary()
print(summary["counters"]["requests_total"])
print(summary["histograms"]["response_time"]["p95"])
```

### Policy Engine

```python
from observability_policy_hub import PolicyEngine, PolicyDecision

# Initialize engine (fail_open=False means deny on error)
engine = PolicyEngine(fail_open=False)

# Define a rule
def check_load(context):
    if context.get("load", 0) > 80:
        return PolicyDecision(allow=False, reason="load_too_high")
    return PolicyDecision(allow=True)

# Register rule
engine.register_rule("check_load", check_load)

# Evaluate
context = {"load": 85, "user": "admin"}
decision = engine.evaluate(context)

if decision.allow:
    print("Allowed")
else:
    print(f"Denied: {decision.reason}")
```

## Development

To run tests:

```bash
pip install pytest
pytest tests/
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=observability-policy-hub
```

## Usage

```python
import observability_policy_hub
```

## Configuration

Policy hub is configured programmatically via `MetricRegistry` and `PolicyEngine`
constructor options and rule registration.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
