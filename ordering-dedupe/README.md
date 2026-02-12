# Ordering & Deduplication

Lightweight sequencing and deduplication primitives for resilient message handling.

## Features

- **Deduplicator**: TTL-based, thread-safe dedupe with bounded capacity.
- **Sequencer**: Issue monotonically increasing sequence numbers.
- **Stateless reorder**: Sort batched items by sequence.

## Usage

```python
from ordering_dedupe import Deduplicator, Sequencer

sequencer = Sequencer()
message_seq = sequencer.issue()

# Deduplicate by id
dedupe = Deduplicator(ttl_seconds=300.0, max_count=10000)
if not dedupe.seen("msg-123"):
    print("Process message")

# Reorder a batch
batch = [(2, "b"), (1, "a"), (3, "c")]
ordered = Sequencer.reorder(batch)
print(ordered)  # ['a', 'b', 'c']
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=ordering-dedupe
```

## Usage

```python
import ordering_dedupe
```

## Configuration

Configure deduplication via `Deduplicator` TTL and capacity settings, and sequencing
via `Sequencer` initialization.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
