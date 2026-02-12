#!/usr/bin/env python3
"""
Stub server for testing the sample consumer.
Simulates a backend service that supports multiple protocols (mocked via simple TCP)
and can simulate failures to trigger retry/fallback logic.
"""

import socket
import threading
import time
import logging
import argparse
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[Server] %(message)s')
logger = logging.getLogger(__name__)

class StubServer:
    """
    A simple TCP server stub that echoes received messages.
    Can be configured to fail (close connection) to test client resilience.
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.failure_mode = False  # If True, closes connection immediately

    def start(self) -> None:
        """Starts the server in a background thread."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        self.running = True
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
        logger.info(f"Listening on {self.host}:{self.port}")

    def stop(self) -> None:
        """Stops the server and closes the socket."""
        self.running = False
        if self.sock:
            # Connect to self to unblock accept() if needed, or just close
            # Closing socket while accept() is blocking raises OSError, which we catch.
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("Stopped.")

    def _accept_loop(self) -> None:
        """Internal loop to accept connections."""
        while self.running and self.sock:
            try:
                conn, addr = self.sock.accept()
                with conn:
                    logger.info(f"Connection from {addr}")
                    if self.failure_mode:
                        logger.info("Simulating failure (closing connection)")
                        continue
                    
                    data = conn.recv(1024)
                    if data:
                        decoded = data.decode('utf-8')
                        logger.info(f"Received: {decoded}")
                        response = f"Ack: {decoded}"
                        conn.sendall(response.encode('utf-8'))
            except OSError:
                # Socket closed or other error
                if self.running:
                    logger.warning("Socket error in accept loop.")
                break
            except Exception as e:
                logger.error(f"Error in accept loop: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="Stub TCP Server for Resilience Testing")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--fail", action="store_true", help="Start in failure mode")
    return parser.parse_args()

def main():
    args = parse_args()
    server = StubServer(host=args.host, port=args.port)
    server.failure_mode = args.fail
    
    try:
        server.start()
        print("Server running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()