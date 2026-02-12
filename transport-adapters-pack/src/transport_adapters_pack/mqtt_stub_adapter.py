from __future__ import annotations

import logging
from typing import Any, Dict

from .base import TransportAdapter, TransportResponse

logger = logging.getLogger(__name__)


class MqttStubAdapter(TransportAdapter):
    """
    Stub adapter for MQTT.
    
    This adapter simulates MQTT behavior for testing purposes without requiring a broker.
    """
    
    name = "mqtt"

    def supports(self, capabilities: Dict[str, Any]) -> bool:
        return capabilities.get("mqtt", False)

    def send(self, request: Dict[str, Any]) -> TransportResponse:
        """
        Simulate sending an MQTT message.
        
        Args:
            request: Must contain 'topic'. Optional 'payload'.
        """
        topic = request.get("topic", "")
        payload = request.get("payload")
        
        logger.info(f"MQTT STUB: Publishing to {topic} with payload length {len(str(payload)) if payload else 0}")
        
        # In a real MQTT adapter, this would publish to a broker.
        # Here we just echo back a success status.
        return TransportResponse(
            status=0,
            body={"topic": topic, "payload": payload, "status": "published"}
        )