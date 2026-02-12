"""Connection multiplexer package for resilient transport management."""

from .errors import MultiplexingError, TransportError
from .transports import Transport, SimulatedTransport
from .multiplexer import ConnectionMultiplexer, TransportRegistryEntry

__all__ = [
    "MultiplexingError",
    "TransportError",
    "Transport",
    "SimulatedTransport",
    "ConnectionMultiplexer",
    "TransportRegistryEntry",
]
