from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .exceptions import TransportError


@dataclass
class TransportResponse:
    """Standardized response from a transport adapter."""
    status: int
    body: Any
    headers: Optional[Dict[str, str]] = None


class TransportAdapter(ABC):
    """Abstract base class for all transport adapters."""
    
    name: str = "base"

    @abstractmethod
    def supports(self, capabilities: Dict[str, Any]) -> bool:
        """
        Check if the adapter supports the given capabilities.
        
        Args:
            capabilities: A dictionary of capability requirements.
            
        Returns:
            True if supported, False otherwise.
        """
        return True

    @abstractmethod
    def send(self, request: Dict[str, Any]) -> TransportResponse:
        """
        Send a request via the transport.
        
        Args:
            request: A dictionary containing request details (e.g. 'payload', 'topic', 'url').
            
        Returns:
            TransportResponse: The response from the transport.
            
        Raises:
            TransportError: If the transmission fails.
        """
        pass

    def close(self) -> None:
        """Clean up resources."""
        pass
