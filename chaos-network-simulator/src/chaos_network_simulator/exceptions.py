class ChaosError(Exception):
    """Base exception for chaos-network-simulator errors."""
    pass

class ChaosConfigurationError(ChaosError):
    """Raised when scenario configuration is invalid."""
    pass

class SimulatedFaultError(ChaosError):
    """Raised when a simulated fault occurs."""
    pass
