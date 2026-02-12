class ProtocolFallbackError(Exception):
    """Base exception for protocol fallback layer."""
    pass


class NoCompatibleAdapterError(ProtocolFallbackError):
    """Raised when no adapter supports the required capabilities."""
    pass


class AllAdaptersFailedError(ProtocolFallbackError):
    """Raised when all compatible adapters failed to process the request."""
    def __init__(self, errors: list[Exception]):
        self.errors = errors
        super().__init__(f"All adapters failed. Errors: {errors}")
