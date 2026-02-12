import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class TransportError(Exception):
    """Raised when a transport fails to send or operate.
    
    Attributes:
        message: Human-readable error description
        transport_name: Name of the transport that failed
        retryable: Whether the error is transient and retryable
    """

    def __init__(self, message: str, transport_name: Optional[str] = None, retryable: bool = True):
        super().__init__(message)
        self.transport_name = transport_name
        self.retryable = retryable
        logger.debug(f"Transport error: {message} (transport={transport_name}, retryable={retryable})")


class MultiplexingError(Exception):
    """Raised when the multiplexer cannot deliver through any transport.
    
    Indicates exhaustion of all available transport strategies. Includes details
    of which transports were attempted.
    
    Attributes:
        message: Human-readable error description
        attempted: List of transport names that were attempted
        last_error: The final error encountered before giving up
    """

    def __init__(self, message: str, attempted: Optional[List[str]] = None, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.attempted = attempted or []
        self.last_error = last_error
        logger.warning(f"Multiplexing failed after {len(self.attempted)} attempts: {message}")
