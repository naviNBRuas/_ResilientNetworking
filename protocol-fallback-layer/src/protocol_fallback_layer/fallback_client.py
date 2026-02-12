from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Iterable, List, Optional

from .adapter import ProtocolAdapter, RequestT, ResponseT
from .exceptions import AllAdaptersFailedError, NoCompatibleAdapterError
from .policy import FallbackPolicy, PriorityListPolicy

logger = logging.getLogger(__name__)


@dataclass
class FallbackResult(Generic[ResponseT]):
    response: ResponseT
    chosen: str
    attempted: List[str]
    errors: Dict[str, Exception] = field(default_factory=dict)


class FallbackClient(Generic[RequestT, ResponseT]):
    """
    Client that orchestrates protocol fallback.
    """

    def __init__(
        self, 
        adapters: Iterable[ProtocolAdapter[RequestT, ResponseT]],
        policy: Optional[FallbackPolicy] = None
    ):
        """
        Initialize the FallbackClient.

        Args:
            adapters: A list or iterable of available protocol adapters.
            policy: The fallback policy to use. Defaults to PriorityListPolicy.
        """
        self.adapters = list(adapters)
        self.policy = policy or PriorityListPolicy()
        self.state: Dict[str, Any] = {}

    def send(self, request: RequestT, capabilities: Optional[Dict[str, Any]] = None) -> FallbackResult[ResponseT]:
        """
        Send a request, falling back through adapters as determined by the policy.

        Args:
            request: The request to send.
            capabilities: Optional capabilities context. Defaults to empty dict.

        Returns:
            FallbackResult containing the response and metadata.

        Raises:
            NoCompatibleAdapterError: If no adapters support the capabilities.
            AllAdaptersFailedError: If all suitable adapters fail.
        """
        capabilities = capabilities or {}
        attempted: List[str] = []
        errors: Dict[str, Exception] = {}
        
        # Get the execution plan from the policy
        plan = list(self.policy.plan(self.adapters, capabilities))
        
        if not plan:
            logger.error("No compatible adapter found for capabilities: %s", capabilities)
            raise NoCompatibleAdapterError(f"No adapter found for capabilities: {capabilities}")

        for adapter in plan:
            adapter_name = adapter.name
            logger.info("Attempting to send request using adapter: %s", adapter_name)
            attempted.append(adapter_name)
            
            try:
                response = adapter.send(request, self.state)
                logger.info("Successfully sent request using adapter: %s", adapter_name)
                return FallbackResult(
                    response=response, 
                    chosen=adapter_name, 
                    attempted=attempted,
                    errors=errors
                )
            except Exception as exc:
                logger.warning("Adapter %s failed: %s", adapter_name, exc)
                errors[adapter_name] = exc
                continue

        logger.error("All adapters failed. Attempted: %s", attempted)
        raise AllAdaptersFailedError(list(errors.values()))

    def close(self) -> None:
        """
        Close all adapters and clear state.
        """
        logger.info("Closing FallbackClient")
        for adapter in self.adapters:
            try:
                adapter.close(self.state)
            except Exception as exc:
                logger.error("Error closing adapter %s: %s", adapter.name, exc)