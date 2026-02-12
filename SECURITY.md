# Security Best Practices

## Input Validation

### Core Principle
**Never trust external input.** Validate all inputs at module boundaries.

### Transport Names
```python
# ❌ Bad
def register(self, name: str, transport: Transport) -> None:
    self.transports[name] = transport

# ✅ Good
import re

def register(self, name: str, transport: Transport) -> None:
    if not name or not name.strip():
        raise ValueError("Transport name must not be empty")
    if len(name) > 255:
        raise ValueError("Transport name too long (max 255 chars)")
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError("Transport name must be alphanumeric with _ and -")
    self.transports[name] = transport
```

### Payload Validation
```python
# ❌ Bad
def send(self, payload):
    return self._transport.send(payload)

# ✅ Good
def send(self, payload, *, max_size_bytes=10*1024*1024):
    if payload is None:
        raise ValueError("Payload cannot be None")
    
    # Check size to prevent DoS
    payload_size = len(json.dumps(payload))
    if payload_size > max_size_bytes:
        raise ValueError(f"Payload too large: {payload_size} > {max_size_bytes}")
    
    # Validate structure if expected
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dict")
    
    return self._transport.send(payload)
```

### URL & Credential Validation
```python
from urllib.parse import urlparse
import re

# ❌ Bad
def connect(self, url: str) -> None:
    self.connection = requests.get(url)

# ✅ Good
def connect(self, url: str) -> None:
    # Parse and validate URL
    parsed = urlparse(url)
    
    # Only allow certain schemes
    if parsed.scheme not in ('http', 'https', 'ws', 'wss'):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    
    # Prevent SSRF attacks: disallow private IPs
    if parsed.hostname in ('localhost', '127.0.0.1', '0.0.0.0'):
        raise ValueError("Cannot connect to localhost (potential SSRF)")
    
    # Check against private IP ranges
    import ipaddress
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private:
            raise ValueError(f"Private IP not allowed: {ip}")
    except ValueError:
        pass  # Not an IP address, assume domain is OK
    
    self.connection = requests.get(url, timeout=5)
```

## Secrets Management

### Never Hardcode Secrets
```python
# ❌ Bad
HMAC_KEY = "super-secret-key-12345"

# ✅ Good
import os
HMAC_KEY = os.environ.get('HMAC_KEY')
if not HMAC_KEY:
    raise RuntimeError("HMAC_KEY environment variable not set")
```

### Secure Storage
```python
# Option 1: Environment variables
# export RESILIENT_NETWORKING_HMAC_KEY=$(openssl rand -hex 32)

# Option 2: Secret management system
from aws_secretsmanager_caching import SecretCache
cache = SecretCache()
hmac_key = cache.get_secret_string('resilient-networking/hmac-key')

# Option 3: File with restricted permissions
# /etc/resilient-networking/secrets.json (mode 0600)
import json
with open('/etc/resilient-networking/secrets.json', 'r') as f:
    secrets = json.load(f)
hmac_key = secrets['hmac_key']
```

### Key Rotation
```python
from crypto_envelope import EnvelopeVerifier
import datetime

class KeyRotatingVerifier:
    def __init__(self):
        self.current_key = os.environ.get('HMAC_KEY')
        self.previous_key = os.environ.get('HMAC_KEY_PREVIOUS')
        self.key_rotation_date = datetime.datetime.now()
    
    def verify(self, data, signature):
        # Try current key first
        try:
            return EnvelopeVerifier().verify(data, signature, self.current_key)
        except ValueError:
            # Fall back to previous key during rotation period
            if self.previous_key:
                return EnvelopeVerifier().verify(data, signature, self.previous_key)
            raise
    
    def rotate_key(self, new_key):
        self.previous_key = self.current_key
        self.current_key = new_key
```

## Cryptography

### Use Established Algorithms
```python
# ❌ Bad: Custom encryption
def encrypt(data, key):
    return bytes([ord(c) ^ ord(k) for c, k in zip(data, key * 1000)])

# ✅ Good: Use cryptography library
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)
encrypted = cipher.encrypt(data.encode())
decrypted = cipher.decrypt(encrypted).decode()
```

### Signing & Verification
```python
# ❌ Bad: MD5 or custom hash
import hashlib
def sign(data, key):
    return hashlib.md5(data + key).digest()

# ✅ Good: Use HMAC-SHA256
import hmac
import hashlib

def sign(data: bytes, key: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()

def verify(data: bytes, signature: bytes, key: bytes) -> bool:
    expected = hmac.new(key, data, hashlib.sha256).digest()
    return hmac.compare_digest(signature, expected)
```

### TLS/SSL Configuration
```python
# ❌ Bad: No SSL verification
import requests
response = requests.get('https://api.example.com', verify=False)

# ✅ Good: Verify certificates
response = requests.get(
    'https://api.example.com',
    verify=True,  # Verify server certificate
    cert=('/path/to/client.crt', '/path/to/client.key')  # Client cert
)

# Custom CA bundle for internal PKI
response = requests.get(
    'https://api.example.com',
    verify='/etc/ssl/certs/internal-ca.pem'
)
```

## Access Control

### Authentication
```python
from functools import wraps
import jwt

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
            request.user = payload
        except jwt.InvalidTokenError:
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/send', methods=['POST'])
@require_auth
def send_message():
    # Only authenticated users can send
    pass
```

### Authorization
```python
def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if permission not in request.user.get('permissions', []):
                return {'error': 'Forbidden'}, 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/api/admin/config', methods=['POST'])
@require_auth
@require_permission('admin')
def update_config():
    # Only users with 'admin' permission can update config
    pass
```

## Error Handling Security

### Information Disclosure
```python
# ❌ Bad: Leaks internal details
try:
    result = unreliable_operation()
except Exception as e:
    return {'error': str(e)}, 500

# ✅ Good: Generic error message + logging
import logging
logger = logging.getLogger(__name__)

try:
    result = unreliable_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    return {'error': 'Operation failed'}, 500
```

### Stack Trace Exposure
```python
# ❌ Bad: Returns stack trace to client
try:
    risky_operation()
except Exception as e:
    return {
        'error': str(e),
        'traceback': traceback.format_exc()
    }, 500

# ✅ Good: Log trace, return generic error
try:
    risky_operation()
except Exception as e:
    logger.exception("Request failed")  # Logs traceback
    return {'error': 'Internal error'}, 500
```

## Dependency Security

### Dependency Scanning
```bash
# Check for known vulnerabilities
pip install safety
safety check

# Generate SBOM (Software Bill of Materials)
pip install cyclonedx-bom
cyclonedx-py -o sbom.xml
```

### Dependency Pinning
```toml
[project]
dependencies = [
    "cryptography>=38.0.0,<40.0.0",  # Loose pinning: allows bug fixes
    "requests>=2.28.0,<3.0.0",
]

[tool.pip-tools]
unsafe-pin = false  # Prevent pip-tools from generating unsafe locks
```

### License Compliance
```bash
# Check licenses of dependencies
pip install pip-licenses
pip-licenses --format=json --output-file=licenses.json

# Ensure no GPL dependencies in proprietary code
grep -i "GPL" licenses.json
```

## Logging Security

### Don't Log Secrets
```python
# ❌ Bad: Logs sensitive data
logger.info(f"Connecting with token: {api_token}")

# ✅ Good: Mask sensitive data
def mask_token(token, visible_chars=4):
    if len(token) <= visible_chars:
        return "*" * len(token)
    return token[:visible_chars] + "*" * (len(token) - visible_chars)

logger.info(f"Connecting with token: {mask_token(api_token)}")

# ✅ Even better: Omit entirely
logger.info("Connecting to API")
```

### Log Access Control
```bash
# Restrict log file permissions
chmod 600 application.log
chown app:app application.log

# Centralize logs for audit trail
# ELK Stack, Splunk, CloudWatch, etc.
```

## Rate Limiting & DoS Protection

### Request Rate Limiting
```python
from functools import lru_cache
from time import time

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id):
        now = time()
        
        # Clean old requests outside window
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if now - t < self.window_seconds
            ]
        else:
            self.requests[client_id] = []
        
        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        return False

# Use in handler
limiter = RateLimiter(max_requests=100, window_seconds=60)

@app.route('/api/send', methods=['POST'])
def send_message():
    client_id = request.remote_addr
    if not limiter.is_allowed(client_id):
        return {'error': 'Rate limit exceeded'}, 429
    # ... process request
```

### Payload Size Limits
```python
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Timeout for long operations
from signal import signal, SIGALRM, alarm

def timeout_handler(signum, frame):
    raise TimeoutError("Operation exceeded timeout")

signal(SIGALRM, timeout_handler)
alarm(30)  # 30 second timeout
try:
    long_operation()
finally:
    alarm(0)  # Cancel alarm
```

## Security Testing

### Vulnerability Scanning
```bash
# Static analysis for security issues
pip install bandit
bandit -r src/

# Example output:
# >> Issue: Use of exec detected.
#    Severity: CRITICAL, Confidence: HIGH
```

### Fuzzing
```python
from hypothesis import given, strategies as st

@given(
    name=st.text(min_size=1, max_size=255),
    weight=st.floats(min_value=0, max_value=1000)
)
def test_register_fuzzing(name, weight):
    """Fuzz-test register() with random inputs"""
    mux = ConnectionMultiplexer()
    try:
        mux.register(name, DummyTransport(), weight=weight)
    except (ValueError, TypeError) as e:
        # Expected validation errors are OK
        pass
```

### Penetration Testing
```python
# Example: Test for SSRF vulnerability
test_urls = [
    "http://localhost:8080/admin",
    "http://127.0.0.1:22/ssh",
    "http://169.254.169.254/latest/meta-data/",  # AWS metadata
    "http://[::1]:8080/admin",  # IPv6 localhost
]

for url in test_urls:
    try:
        transport.connect(url)
        print(f"VULNERABILITY: Could connect to {url}")
    except ValueError as e:
        print(f"OK: Blocked {url} with {e}")
```

## Compliance

### GDPR (Personal Data)
- Implement data minimization: collect only necessary data
- Provide data export functionality
- Implement right to be forgotten (data deletion)
- Document data processing in privacy policy

### SOC 2 (Security, Availability, Integrity)
- Implement audit logging (see Deployment.md)
- Implement access controls (see above)
- Implement change management
- Regular security assessments

### PCI DSS (Payment Card Industry)
- Never store credit card numbers (use tokenization)
- Encrypt all transmission of card data
- Use TLS 1.2 minimum
- Implement strong access controls

## Incident Response

### Security Incident Procedure
1. **Identify:** Alert on suspicious activity
2. **Isolate:** Stop affected systems
3. **Assess:** Determine scope and impact
4. **Notify:** Alert stakeholders and users if needed
5. **Remediate:** Fix root cause
6. **Verify:** Test fix and redeploy
7. **Review:** Conduct post-mortem

### Example: Suspected Key Compromise
```python
# 1. Stop application accepting new requests
app.state.accepting_requests = False

# 2. Identify affected time window
compromised_at = datetime.datetime(2024, 1, 15, 10, 30)
log_entries = get_logs_after(compromised_at)

# 3. Rotate key
os.environ['HMAC_KEY'] = generate_new_key()
os.environ['HMAC_KEY_PREVIOUS'] = previous_key

# 4. Re-verify all recent operations
for entry in log_entries:
    try:
        verify(entry['data'], entry['signature'])
    except ValueError:
        # Suspicious: log for investigation
        logger.error(f"Failed verification: {entry}")

# 5. Resume operation
app.state.accepting_requests = True
```

## Security Checklist

- [ ] All inputs validated at module boundaries
- [ ] No hardcoded secrets or credentials
- [ ] TLS/SSL enabled for all network communication
- [ ] Authentication and authorization implemented
- [ ] Rate limiting and DoS protection enabled
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies scanned for vulnerabilities
- [ ] Logs are secured and not world-readable
- [ ] Audit logging enabled for compliance
- [ ] Security testing (bandit, fuzzing) passing
- [ ] Regular security updates schedule established
- [ ] Incident response procedure documented
- [ ] Third-party components validated
- [ ] Code review process includes security checks

## Security Contacts

- **Report Vulnerability:** founder@nbr.company
- **Security Team:** founder@nbr.company
- **On-Call:** +1-555-SECURITY
