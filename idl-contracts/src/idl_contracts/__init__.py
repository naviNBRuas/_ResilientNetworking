import json
from pathlib import Path
from typing import Any, Dict

import jsonschema
from importlib import resources

# Define the package name
_PACKAGE_NAME = __package__ or "idl_contracts"

def get_schema_path(schema_name: str) -> Path:
    """
    Returns the absolute path to a schema file.

    Args:
        schema_name (str): The name of the schema (e.g., 'retry_outcome' or 'retry_outcome.json').

    Returns:
        Path: The path to the schema file.

    Raises:
        FileNotFoundError: If the schema file does not exist.
    """
    if not schema_name.endswith(".json"):
        schema_name += ".json"
    
    # Use importlib.resources to find the file within the package
    # We assume schemas are located in the 'schemas' subdirectory of the package
    try:
        # For Python 3.9+ we can use files()
        package_files = resources.files(_PACKAGE_NAME) / "schemas" / schema_name
        with resources.as_file(package_files) as path:
             if not path.exists():
                 raise FileNotFoundError(f"Schema '{schema_name}' not found in package '{_PACKAGE_NAME}'.")
             return path
    except (TypeError, ModuleNotFoundError):
        # Fallback for older python or non-installed usage (e.g. running from source without install)
        # This is a bit of a hack but useful for development
        base_dir = Path(__file__).parent
        schema_path = base_dir / "schemas" / schema_name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema '{schema_name}' not found in '{base_dir}/schemas'.")
        return schema_path

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Loads a JSON schema into a dictionary.

    Args:
        schema_name (str): The name of the schema.

    Returns:
        Dict[str, Any]: The parsed JSON schema.
    """
    path = get_schema_path(schema_name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore

def validate_data(data: Any, schema_name: str) -> None:
    """
    Validates data against a specific schema.

    Args:
        data (Any): The data to validate.
        schema_name (str): The name of the schema to validate against.

    Raises:
        jsonschema.ValidationError: If validation fails.
        FileNotFoundError: If the schema is not found.
    """
    schema = load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)
