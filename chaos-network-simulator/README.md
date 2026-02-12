# chaos-network-simulator

Controlled fault-injection and network-behavior simulation tool to validate resilience strategies. Enables reproducible scenarios for latency, loss, jitter, partitions, throttling, and protocol-level failures.

## Scope
- Scenario definition language/config for network conditions and failure modes.
- Execution engine to run scenarios against targets or harnessed modules.
- Metrics capture and reporting for SLO/SLA validation under stress.
- Integrations with CI to gate changes on resilience regressions.

## Deliverables (incremental)
- Scenario spec format and parser.
- Executors for local (loopback) and containerized/remote targets.
- Visualization/reporting hooks for run results.
- Example scenarios covering common degradations and rare-but-impactful events.

## Consumption
- **Library:** Embed scenario runners into your test harness.
- **CLI/service:** Run standalone to exercise systems under test.
- Versioned via tags like `chaos-network-simulator/v0.1.0`; pin to tags/SHAs.

## Getting started (placeholder)
- Scenario spec, runner, and example suites will be added here.
- CI examples will follow once runners are in place.

## Status
Scaffold ready. Implementation to follow with focus on deterministic, reproducible simulations.

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=chaos-network-simulator
```

## Usage

```python
import chaos_network_simulator
```

## Configuration

Scenario definitions are configured via scenario specs and runner settings. Refer to
module documentation for the supported schema.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.