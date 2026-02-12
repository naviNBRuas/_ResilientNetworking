from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict

from .exceptions import RolloutError


@dataclass
class FeatureFlag:
    """Represents a feature flag configuration."""
    name: str
    percentage: float = 0.0  # 0-100

    def __post_init__(self) -> None:
        if not (0.0 <= self.percentage <= 100.0):
            raise RolloutError(f"Flag '{self.name}' percentage must be between 0 and 100, got {self.percentage}")

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> FeatureFlag:
        """
        Creates a FeatureFlag instance from a dictionary.

        Args:
            name: The name of the flag.
            data: A dictionary containing flag configuration (e.g., {"percentage": 50.0}).

        Returns:
            A FeatureFlag instance.

        Raises:
            RolloutError: If the configuration is invalid.
        """
        try:
            percentage = float(data.get("percentage", 0.0))
            return cls(name=name, percentage=percentage)
        except (ValueError, TypeError) as e:
            raise RolloutError(f"Invalid configuration for flag '{name}': {e}") from e


class RolloutEngine:
    """
    Evaluates feature flags to determine if a feature should be enabled.
    """

    def __init__(self, flags: Dict[str, FeatureFlag]):
        """
        Args:
            flags: A dictionary of FeatureFlag objects keyed by flag name.
        """
        self.flags = flags

    def enabled(self, flag_name: str, identifier: str | None = None) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: The name of the feature flag.
            identifier: An optional unique identifier (e.g., user ID, session ID)
                        to ensure deterministic evaluation. If None, the result
                        is random (non-deterministic).

        Returns:
            True if the feature is enabled, False otherwise.
        """
        flag = self.flags.get(flag_name)
        if not flag:
            return False

        if flag.percentage >= 100.0:
            return True
        if flag.percentage <= 0.0:
            return False

        if identifier is None:
            # Fallback to pure random if no identifier provided (non-deterministic)
            import random
            return random.uniform(0, 100) < flag.percentage

        # Deterministic hashing based on flag name and identifier
        # This ensures the same user always gets the same result for the same flag
        key = f"{flag_name}:{identifier}".encode("utf-8")
        hash_val = int(hashlib.sha256(key).hexdigest(), 16)
        
        # Map hash to 0-100 scale
        # Use last 4 digits of hash for sufficient granularity (0-9999)
        normalized = (hash_val % 10000) / 100.0
        
        return normalized < flag.percentage


def parse_feature_flags(config: Dict[str, Any]) -> Dict[str, FeatureFlag]:
    """
    Parses a dictionary of feature flags configuration.

    Args:
        config: A dictionary where keys are flag names and values are 
                configuration dictionaries (containing 'percentage').

    Returns:
        A dictionary mapping flag names to FeatureFlag objects.
    
    Raises:
        RolloutError: If any flag configuration is invalid.
    """
    flags = {}
    for name, data in config.items():
        if isinstance(data, dict):
            flags[name] = FeatureFlag.from_dict(name, data)
    return flags
