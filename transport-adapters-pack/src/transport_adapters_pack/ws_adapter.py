from __future__ import annotations

import logging
from typing import Any, Dict

from .base import TransportAdapter, TransportResponse

logger = logging.getLogger(__name__)


class WebSocketAdapter(TransportAdapter):
    """
    Stub adapter for WebSocket.
    
    This adapter simulates WebSocket behavior.
    """
    
    name = "websocket"

    def supports(self, capabilities: Dict[str, Any]) -> bool:
        return capabilities.get("websocket", False)

    def send(self, request: Dict[str, Any]) -> TransportResponse:
        """
        Simulate sending a message over WebSocket.
        """
        payload = request.get("payload", "")
        logger.info(f"WS STUB: Sending message, payload length {len(str(payload))}")
        
        return TransportResponse(
            status=101, # Switching Protocols / Open
            body={"message": payload, "status": "sent"}
        )