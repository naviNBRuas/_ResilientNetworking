import socket
import time
import pytest
from sample_consumers.examples.server_stub import StubServer

@pytest.fixture
def stub_server():
    # Use port 0 to let OS choose a free port to avoid conflicts
    server = StubServer(port=0)
    server.start()
    # Wait a bit for server to start (though start() is fast, the thread needs to be ready)
    time.sleep(0.1)
    # Update port because it was 0
    server.port = server.sock.getsockname()[1]
    yield server
    server.stop()

def test_server_echo(stub_server):
    host, port = stub_server.host, stub_server.port
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        msg = "Hello Server"
        s.sendall(msg.encode('utf-8'))
        data = s.recv(1024)
    
    assert data.decode('utf-8') == f"Ack: {msg}"

def test_server_failure_mode(stub_server):
    stub_server.failure_mode = True
    host, port = stub_server.host, stub_server.port
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        # It accepts connection but then closes it or doesn't send data?
        # In code: if self.failure_mode: continue (loop), so it closes `conn` because of `with conn:` scope exit?
        # Yes, `with conn:` block ends immediately after continue.
        
        # So sending might succeed (buffered), but recv should return empty bytes (EOF).
        try:
            s.sendall(b"test")
            data = s.recv(1024)
            assert data == b"" # EOF
        except (ConnectionResetError, BrokenPipeError):
            pass # Acceptable behavior
