from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict

from .base import TransportAdapter, TransportResponse
from .exceptions import (
    ConnectionError,
    TransportError,
    TimeoutError as TransportTimeoutError,
    ProtocolError,
)

logger = logging.getLogger(__name__)


class HttpAdapter(TransportAdapter):
    """
    Standard HTTP adapter using the standard library (urllib).

    Can be initialized with a base_url.
    """

    name = "http"

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    def supports(self, capabilities: Dict[str, Any]) -> bool:
        return capabilities.get("http", True)

    def _build_url(self, request: Dict[str, Any]) -> str:
        url = request.get("url")
        if not url:
            path = request.get("path", "")
            if not path.startswith("/"):
                path = "/" + path
            
            if not self.base_url:
                if not path.startswith("http"):
                    raise ProtocolError("No valid URL provided (base_url empty and path is not a URL).")
                url = path
            else:
                url = f"{self.base_url}{path}"
        
        params = request.get("params")
        if params:
            url_parts = list(urllib.parse.urlparse(url))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urllib.parse.urlencode(query)
            url = urllib.parse.urlunparse(url_parts)
            
        return url

    def _prepare_body(self, body: Any, headers: Dict[str, str]) -> bytes | None:
        if body is None:
            return None
            
        if isinstance(body, dict):
            headers["Content-Type"] = "application/json"
            return json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            return body.encode("utf-8")
        elif isinstance(body, bytes):
            return body
        else:
            return str(body).encode("utf-8")

    def _decode_response(self, response_body: bytes, content_type: str) -> Any:
        # Determine encoding from content-type or default to utf-8
        # Simple implementation: check for charset
        encoding = "utf-8" # default
        if "charset=" in content_type:
            try:
                encoding = content_type.split("charset=")[-1].split(";")[0].strip()
            except IndexError:
                pass
        
        decoded_str = response_body.decode(encoding, errors="replace")

        if "application/json" in content_type:
            try:
                return json.loads(decoded_str)
            except json.JSONDecodeError:
                logger.warning("Failed to decode JSON response")
                return decoded_str
        
        return decoded_str

    def send(self, request: Dict[str, Any]) -> TransportResponse:
        """
        Send an HTTP request.

        Request dict keys:
            - url (str): Full URL (overrides base_url + path).
            - path (str): Path to append to base_url (if url not provided).
            - params (dict): Query parameters.
            - method (str): HTTP method (default: GET).
            - headers (dict): HTTP headers.
            - body (Any): Request body. If dict, sent as JSON.
            - timeout (float): Timeout in seconds.
        """
        url = self._build_url(request)
        method = request.get("method", "GET").upper()
        headers = request.get("headers", {}).copy()
        body = request.get("body")
        timeout = request.get("timeout", 10.0)

        data = self._prepare_body(body, headers)

        logger.debug(f"Sending {method} request to {url}")
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                resp_headers = dict(response.getheaders())
                resp_body = response.read()
                content_type = resp_headers.get("Content-Type", "").lower()
                
                decoded_body = self._decode_response(resp_body, content_type)

                return TransportResponse(status=status, body=decoded_body, headers=resp_headers)

        except urllib.error.HTTPError as e:
            resp_body = e.read()
            content_type = e.headers.get("Content-Type", "").lower()
            decoded_body = self._decode_response(resp_body, content_type) if resp_body else str(e.reason)
            
            return TransportResponse(status=e.code, body=decoded_body, headers=dict(e.headers))

        except urllib.error.URLError as e:
            # e.reason can be a socket.timeout or TimeoutError
            if isinstance(e.reason, TimeoutError): # Builtin TimeoutError
                raise TransportTimeoutError(f"Request timed out: {e.reason}") from e
            if isinstance(e.reason,  OSError) and "timeout" in str(e.reason).lower(): # socket.timeout is subclass of OSError
                 raise TransportTimeoutError(f"Request timed out: {e.reason}") from e

            raise ConnectionError(f"Network error: {e.reason}") from e
            
        except TimeoutError as e: # Catch builtin TimeoutError if raised directly
             raise TransportTimeoutError(f"Request timed out: {e}") from e

        except Exception as e:
             logger.exception("Unexpected error in HttpAdapter")
             raise TransportError(f"Unexpected error: {e}") from e