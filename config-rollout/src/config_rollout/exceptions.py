class ConfigRolloutError(Exception):
    """Base exception for config-rollout."""
    pass


class ConfigError(ConfigRolloutError):
    """Raised when configuration loading fails."""
    pass


class RolloutError(ConfigRolloutError):
    """Raised when rollout operations fail."""
    pass
