from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class ProtocolAdapter(ABC, Generic[RequestT, ResponseT]):
    """
    Abstract base class for protocol adapters.
    
    Adapters are responsible for:
    1. Checking if they support the given capabilities.
    2. Sending a request using a specific protocol.
    3. Cleaning up resources.
    """
    name: str

    @abstractmethod
    def supports(self, capabilities: Dict[str, Any]) -> bool:
        """
        Check if the adapter supports the given capabilities.
        
        Args:
            capabilities: A dictionary of capabilities (e.g., {"http2": True}).
            
        Returns:
            True if supported, False otherwise.
        """
        ...

    @abstractmethod
    def send(self, request: RequestT, state: Dict[str, Any]) -> ResponseT:
        """
        Send a request using the adapter's protocol.
        
        Args:
            request: The request payload.
            state: A dictionary for maintaining session state across fallbacks.
            
        Returns:
            The response from the protocol.
            
        Raises:
            Exception: If the transmission fails.
        """
        ...

    @abstractmethod
    def close(self, state: Dict[str, Any]) -> None:
        """
        Clean up any resources associated with the adapter or state.
        
        Args:
            state: The shared session state.
        """
        ...