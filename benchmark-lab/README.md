# Benchmark Lab

A lightweight, robust microbenchmarking harness for Python, designed for resilience components and performance-critical code.

## Features

- **Simple API**: Easy to drop into existing codebases.
- **Robust Statistics**: Reports Min, Max, Average, Median, p95, p99, and Standard Deviation.
- **Warmup Support**: Automatically runs warmup iterations to stabilize JIT/cache.
- **GC Control**: Option to disable garbage collection during measurement for reduced jitter.
- **Type Hinted**: Fully typed for better IDE support and static analysis.

## Installation

```bash
pip install benchmark-lab
```

*Note: If installing from source:*
```bash
pip install .
```

## Usage

### Basic Example

```python
import time
from benchmark_lab import BenchmarkRunner

def work_to_measure(duration=0.01):
    time.sleep(duration)

# Initialize runner
# iterations: Number of times to run the measurement
# warmup: Number of times to run before measurement (discarded)
runner = BenchmarkRunner(iterations=100, warmup=10)

# Run benchmark
result = runner.run(work_to_measure, duration=0.005)

# Print report
print(result)
```

**Output:**
```
BenchmarkResult(
  samples=100,
  avg=5.1234 ms,
  min=5.0012 ms,
  max=5.5432 ms,
  median=5.0500 ms,
  p95=5.2000 ms,
  p99=5.4000 ms,
  stddev=0.1000 ms
)
```

### Advanced Usage

To reduce noise from the garbage collector during microbenchmarks:

```python
runner = BenchmarkRunner(iterations=1000, disable_gc=True)
result = runner.run(my_function)
```

## API Reference

### `BenchmarkRunner`

```python
class BenchmarkRunner(iterations: int = 1000, warmup: int = 5, disable_gc: bool = False)
```

- `iterations`: Number of measured executions.
- `warmup`: Number of unmeasured executions prior to the main loop.
- `disable_gc`: If `True`, `gc.disable()` is called before the measurement loop and `gc.enable()` is restored afterwards.

#### Methods

- `run(fn, *args, **kwargs) -> BenchmarkResult`: Executes `fn(*args, **kwargs)` the specified number of times and returns a result object.

### `BenchmarkResult`

Data class holding the list of `samples` (timings in seconds). Provides properties for statistics in milliseconds:

- `min_ms`, `max_ms`
- `avg_ms` (Mean)
- `median_ms`
- `p95_ms`, `p99_ms` (Percentiles)
- `stddev_ms` (Standard Deviation)
- `total_time` (Total duration of all samples in seconds)

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=benchmark-lab
```

## Usage

```python
from benchmark_lab import BenchmarkRunner
```

## Configuration

Benchmark behavior is configured via `BenchmarkRunner` parameters (iterations, warmup,
and GC control).

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
