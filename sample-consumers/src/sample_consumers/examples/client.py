#!/usr/bin/env python3
"""
Sample client composing connection-multiplexer, adaptive-retry-strategy, and protocol-fallback-layer.
"""

import logging
from typing import Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='[Client] %(message)s')
logger = logging.getLogger(__name__)

# Try imports, fall back to mocks
try:
    from connection_multiplexer import ConnectionMultiplexer
    from adaptive_retry_strategy import AdaptiveRetryStrategy
    from protocol_fallback_layer import ProtocolFallbackLayer
    logger.info("Successfully imported resilience modules.")
except ImportError:
    logger.warning("Could not import resilience modules. Using internal Mocks.")
    try:
        from sample_consumers.mocks import (
            MockConnectionMultiplexer as ConnectionMultiplexer,
            MockAdaptiveRetryStrategy as AdaptiveRetryStrategy,
            MockProtocolFallbackLayer as ProtocolFallbackLayer,
        )
    except ImportError:
        # Fallback for direct execution if package not installed
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
        from sample_consumers.mocks import (
            MockConnectionMultiplexer as ConnectionMultiplexer,
            MockAdaptiveRetryStrategy as AdaptiveRetryStrategy,
            MockProtocolFallbackLayer as ProtocolFallbackLayer,
        )

class ResilientClient:
    """
    A client that demonstrates resilient networking patterns by composing
    Multiplexer, Retry, and Fallback layers.
    """

    def __init__(
        self,
        multiplexer: Optional[Any] = None,
        retry_strategy: Optional[Any] = None,
        fallback_layer: Optional[Any] = None
    ):
        """
        Initialize the ResilientClient with optional injected dependencies.
        
        Args:
            multiplexer: Instance handling transport (e.g. ConnectionMultiplexer)
            retry_strategy: Instance handling retries (e.g. AdaptiveRetryStrategy)
            fallback_layer: Instance handling protocol fallback (e.g. ProtocolFallbackLayer)
        """
        self.multiplexer = multiplexer or ConnectionMultiplexer()
        self.retry = retry_strategy or AdaptiveRetryStrategy(max_retries=2, backoff_factor=0.5)
        self.fallback = fallback_layer or ProtocolFallbackLayer(primary_protocol="tcp", fallback_protocol="udp")

    def send_message(self, message: str) -> None:
        """
        Composes the layers to send a message.
        Structure: Fallback -> Retry -> Multiplexer
        
        Args:
            message: The string payload to send.
        """
        logger.info(f"Client: initiating send for '{message}'")
        
        def attempt_send(payload: str, protocol: str) -> Any:
            """
            Inner function to wrap the multiplexer send with retry logic.
            This is passed to the fallback layer.
            """
            # The fallback layer provides the protocol.
            # We wrap the multiplexer's send method with the retry strategy.
            return self.retry.execute(self.multiplexer.send, payload, protocol=protocol)

        try:
            self.fallback.execute(attempt_send, message)
            logger.info("Client: Message delivered successfully.")
        except Exception as e:
            logger.error(f"Client: Failed to deliver message. Error: {e}")
            raise  # Re-raise to let caller handle or be aware of total failure

def main():
    """
    Demonstration entry point.
    """
    client = ResilientClient()
    
    # Test 1: Successful send (mock TCP succeeds)
    print("\n--- Test 1: Normal Operation ---")
    try:
        client.send_message("Hello World")
    except Exception:
        pass # Expected success

    # Test 2: Force retry/fallback logic
    print("\n--- Test 2: Primary Protocol Failure ---")
    # Forcing a "bad" primary protocol to trigger fallback
    # Since our mock multiplexer fails on UDP, let's make UDP primary
    
    # Re-instantiate with new configuration for demonstration
    fallback_layer = ProtocolFallbackLayer(primary_protocol="udp", fallback_protocol="tcp")
    client_fail = ResilientClient(fallback_layer=fallback_layer)
    
    try:
        client_fail.send_message("Critical Alert")
    except Exception:
        pass # Expected success after fallback

if __name__ == "__main__":
    main()
