import json
import unittest
import socket
from unittest.mock import MagicMock, patch
import urllib.error
from transport_adapters_pack import HttpAdapter, MqttStubAdapter, WebSocketAdapter
from transport_adapters_pack.exceptions import TransportError, ConnectionError, TimeoutError as TransportTimeoutError


class TestHttpAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = HttpAdapter(base_url="http://example.com")

    @patch("urllib.request.urlopen")
    def test_http_send_success_json(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.getheaders.return_value = [("Content-Type", "application/json")]
        mock_response.read.return_value = b'{"success": true}'
        
        # Context manager support
        mock_urlopen.return_value.__enter__.return_value = mock_response

        resp = self.adapter.send({"path": "/api/v1/resource", "method": "POST", "body": {"key": "value"}})

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, {"success": True})
        
        # Verify request
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, "http://example.com/api/v1/resource")
        self.assertEqual(req.method, "POST")
        self.assertEqual(req.data, b'{"key": "value"}')

    @patch("urllib.request.urlopen")
    def test_http_send_with_params(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.getheaders.return_value = []
        mock_response.read.return_value = b''
        mock_urlopen.return_value.__enter__.return_value = mock_response

        self.adapter.send({
            "path": "/search",
            "params": {"q": "test", "page": 1}
        })
        
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        # Query params order is not guaranteed in dict but usually preserved in recent python
        # Check if params are in url
        self.assertIn("q=test", req.full_url)
        self.assertIn("page=1", req.full_url)
        self.assertTrue(req.full_url.startswith("http://example.com/search?"))

    @patch("urllib.request.urlopen")
    def test_http_send_error(self, mock_urlopen):
        # Simulate HTTP 404
        error = urllib.error.HTTPError(
            url="http://example.com/404",
            code=404,
            msg="Not Found",
            hdrs={"Content-Type": "text/plain"},
            fp=None
        )
        error.read = MagicMock(return_value=b"Not Found")
        mock_urlopen.side_effect = error

        resp = self.adapter.send({"path": "/404"})
        self.assertEqual(resp.status, 404)
        self.assertEqual(resp.body, "Not Found")

    @patch("urllib.request.urlopen")
    def test_connection_error(self, mock_urlopen):
        # Simulate network error
        mock_urlopen.side_effect = urllib.error.URLError(reason="Name or service not known")
        
        with self.assertRaises(ConnectionError):
            self.adapter.send({"path": "/"})

    @patch("urllib.request.urlopen")
    def test_timeout_error(self, mock_urlopen):
        # Simulate timeout error
        mock_urlopen.side_effect = urllib.error.URLError(reason=socket.timeout())
        
        with self.assertRaises(TransportTimeoutError):
            self.adapter.send({"path": "/"})

    @patch("urllib.request.urlopen")
    def test_timeout_error_builtin(self, mock_urlopen):
        # Simulate timeout error (builtin TimeoutError)
        mock_urlopen.side_effect = urllib.error.URLError(reason=TimeoutError())
        
        with self.assertRaises(TransportTimeoutError):
            self.adapter.send({"path": "/"})


class TestStubs(unittest.TestCase):
    def test_mqtt_stub(self):
        adapter = MqttStubAdapter()
        assert adapter.supports({"mqtt": True})
        resp = adapter.send({"topic": "test", "payload": "123"})
        self.assertEqual(resp.status, 0)
        self.assertEqual(resp.body["topic"], "test")

    def test_ws_adapter(self):
        adapter = WebSocketAdapter()
        assert adapter.supports({"websocket": True})
        resp = adapter.send({"payload": "ping"})
        self.assertEqual(resp.status, 101)
        self.assertEqual(resp.body["message"], "ping")

if __name__ == "__main__":
    unittest.main()