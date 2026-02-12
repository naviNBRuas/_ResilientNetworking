"""
Mock implementations of resilience layers for standalone execution.
"""

import time
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

class MockConnectionMultiplexer:
    def __init__(self):
        self.transports = ["tcp", "udp"]
        
    def send(self, payload: str, protocol: str) -> bool:
        logger.info(f"Multiplexer: Sending '{payload}' via {protocol}...")
        # Simulate network activity
        time.sleep(0.1)
        if protocol == "udp":
             # Simulate unreliability
             logger.warning("Multiplexer: UDP packet lost (simulated)")
             raise ConnectionError("UDP transport failed")
        logger.info("Multiplexer: Send successful")
        return True

class MockAdaptiveRetryStrategy:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def execute(self, func, *args, **kwargs):
        attempts = 0
        while attempts < self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                wait = self.backoff_factor * attempts
                logger.warning(f"RetryStrategy: Attempt {attempts} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        raise Exception("RetryStrategy: All attempts failed")

class MockProtocolFallbackLayer:
    def __init__(self, primary_protocol: str = "tcp", fallback_protocol: str = "udp"):
        self.primary = primary_protocol
        self.fallback = fallback_protocol

    def execute(self, send_func, payload):
        try:
            logger.info(f"FallbackLayer: Trying primary protocol {self.primary}")
            return send_func(payload, self.primary)
        except Exception as e:
            logger.error(f"FallbackLayer: Primary {self.primary} failed: {e}")
            logger.info(f"FallbackLayer: Downgrading to {self.fallback}")
            return send_func(payload, self.fallback)
