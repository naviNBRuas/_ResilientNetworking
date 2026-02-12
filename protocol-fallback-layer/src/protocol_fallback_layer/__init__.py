"""Protocol fallback and negotiation layer."""

from .adapter import ProtocolAdapter
from .exceptions import (
    AllAdaptersFailedError,
    NoCompatibleAdapterError,
    ProtocolFallbackError,
)
from .fallback_client import FallbackClient, FallbackResult
from .policy import FallbackPolicy, PriorityListPolicy

__all__ = [
    "ProtocolAdapter",
    "FallbackClient",
    "FallbackResult",
    "FallbackPolicy",
    "PriorityListPolicy",
    "ProtocolFallbackError",
    "NoCompatibleAdapterError",
    "AllAdaptersFailedError",
]