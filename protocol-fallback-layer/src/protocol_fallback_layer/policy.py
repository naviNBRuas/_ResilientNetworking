from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Iterator

from .adapter import ProtocolAdapter


class FallbackPolicy(ABC):
    """
    Strategy for selecting and ordering protocol adapters.
    """

    @abstractmethod
    def plan(
        self, 
        adapters: Iterable[ProtocolAdapter], 
        capabilities: Dict[str, Any]
    ) -> Iterator[ProtocolAdapter]:
        """
        Yield adapters in the order they should be attempted.
        
        Args:
            adapters: The available adapters.
            capabilities: The current capabilities/context.
            
        Returns:
            An iterator of ProtocolAdapter to try.
        """
        ...


class PriorityListPolicy(FallbackPolicy):
    """
    Simple policy that iterates through the provided adapters in order,
    skipping those that do not support the required capabilities.
    """
    def plan(
        self, 
        adapters: Iterable[ProtocolAdapter], 
        capabilities: Dict[str, Any]
    ) -> Iterator[ProtocolAdapter]:
        for adapter in adapters:
            if adapter.supports(capabilities):
                yield adapter
