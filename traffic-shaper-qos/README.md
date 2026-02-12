# Traffic Shaper QoS

Weighted fair queueing scheduler for priority-aware traffic shaping and QoS control.

## Features

- **WeightedFairScheduler**: Thread-safe WFQ implementation.
- **Multiple queues**: Named queues with configurable weights.
- **Fairness**: Virtual-time scheduling to balance throughput.

## Usage

```python
from traffic_shaper_qos import WeightedFairScheduler

scheduler = WeightedFairScheduler()

scheduler.enqueue("high", {"id": 1}, weight=5.0)
scheduler.enqueue("low", {"id": 2}, weight=1.0)

item = scheduler.dequeue()
print(item)
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=traffic-shaper-qos
```

## Usage

```python
import traffic_shaper_qos
```

## Configuration

Configure queue weights when enqueuing items to tune priority and fairness.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
