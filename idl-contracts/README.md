# idl-contracts

Typed interface definitions (IDL) for cross-language consumption and contract testing. Currently JSON schemas; could be extended to protobuf/OpenAPI as needed.

## Structure
- `src/idl_contracts/schemas/` — JSON schemas for key data structures

## Usage

### Non-Python Stacks
Use the JSON schemas in `src/idl_contracts/schemas/` to validate request/response shapes when integrating resilience layers or for contract testing.

### Python

This package provides utility functions to access schemas and validate data.

#### Installation

```bash
pip install idl-contracts
```

#### Loading Schemas

```python
from idl_contracts import load_schema

# Load the 'retry_outcome' schema as a dict
schema = load_schema("retry_outcome")
print(schema["title"])
```

#### Validating Data

```python
from idl_contracts import validate_data, load_schema
import jsonschema

data = {
    "attempts": 3,
    "result": {"status": "ok"},
    "error": None,
    "duration": 0.123
}

try:
    validate_data(data, "retry_outcome")
    print("Data is valid!")
except jsonschema.ValidationError as e:
    print(f"Validation failed: {e}")
```

#### Getting Schema Paths

If you need the raw file path to a schema:

```python
from idl_contracts import get_schema_path

path = get_schema_path("transport_response")
print(f"Schema located at: {path}")
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=idl-contracts
```

## Usage

```python
import idl_contracts
```

## Configuration

IDL contracts are provided as JSON schemas. Use helper functions to load and
validate data against schemas.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.