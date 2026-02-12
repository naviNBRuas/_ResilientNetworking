# Config Rollout

A typed configuration and gradual rollout library for Python.

## Features

- **Config Loading**: Load JSON configurations from strings or files.
- **Feature Flags**: Define feature flags with percentage-based rollouts (0-100%).
- **Rollout Engine**: Deterministic (sticky) or random rollout evaluation.
- **Typed & Tested**: Fully typed with `mypy` and tested with `pytest`.

## Usage

### 1. Define your configuration

Create a JSON file (e.g., `config.json`) with your feature flags:

```json
{
  "feature_flags": {
    "new_ui": { "percentage": 10.0 },
    "beta_algorithm": { "percentage": 50.0 },
    "maintenance_mode": { "percentage": 0.0 }
  }
}
```

### 2. Load and use in your application

```python
from config_rollout import ConfigLoader, RolloutEngine, parse_feature_flags

# 1. Load configuration
loader = ConfigLoader()
config_data = loader.load_from_file("config.json")

# 2. Parse feature flags from the config
# Assuming flags are under a "feature_flags" key
flags_config = config_data.get("feature_flags", {})
flags = parse_feature_flags(flags_config)

# 3. Initialize the engine
engine = RolloutEngine(flags)

# 4. Check if features are enabled
user_id = "user_123"

if engine.enabled("new_ui", identifier=user_id):
    print("New UI enabled!")
else:
    print("Old UI active.")

# Deterministic checks:
# The same user_id will always get the same result for the same flag (unless percentage changes).
```

## API

### `ConfigLoader`

- `load(content: str) -> Dict[str, Any]`: Parse JSON string.
- `load_from_file(path: Union[str, Path]) -> Dict[str, Any]`: Parse JSON file.

### `FeatureFlag`

- `name`: Name of the flag.
- `percentage`: Rollout percentage (0.0 to 100.0).

### `RolloutEngine`

- `enabled(flag_name: str, identifier: str | None = None) -> bool`:
    - Returns `True` if flag is enabled.
    - If `identifier` is provided, uses deterministic hashing (SHA-256).
    - If `identifier` is `None`, uses random probability.

## Development

```bash
# Run tests
pytest

# Type checking
mypy .

# Linting
ruff check .
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=config-rollout
```

## Usage

```python
import config_rollout
```

## Configuration

Configuration is loaded from JSON strings/files and evaluated via `RolloutEngine`.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
