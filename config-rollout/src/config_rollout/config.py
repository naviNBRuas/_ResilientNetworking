from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Union

from .exceptions import ConfigError


@dataclass
class ConfigLoader:
    """Loads configuration from various sources."""

    def load(self, content: str) -> Dict[str, Any]:
        """
        Parses a JSON string into a configuration dictionary.

        Args:
            content: The JSON string to parse.

        Returns:
            A dictionary containing the configuration.

        Raises:
            ConfigError: If the content is not valid JSON.
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse config JSON: {e}") from e

    def load_from_file(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Loads configuration from a JSON file.

        Args:
            path: The path to the file.

        Returns:
            A dictionary containing the configuration.

        Raises:
            ConfigError: If the file cannot be read or contains invalid JSON.
        """
        file_path = Path(path)
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.load(content)
        except (OSError, UnicodeDecodeError) as e:
            raise ConfigError(f"Failed to read config file '{file_path}': {e}") from e
