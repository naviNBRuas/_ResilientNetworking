class TransportError(Exception):
    """Base exception for all transport errors."""
    pass


class ConnectionError(TransportError):
    """Raised when a connection cannot be established or is lost."""
    pass


class TimeoutError(TransportError):
    """Raised when a specific operation times out."""
    pass


class ProtocolError(TransportError):
    """Raised when the protocol is violated."""
    pass
