# crypto-envelope

A secure, minimal library for signing and encrypting JSON payloads.

## Features

- **Signed Envelopes**: Cleartext payloads with HMAC-SHA256 signatures.
- **Encrypted Envelopes**: Authenticated encryption using Fernet (AES-128-CBC + HMAC-SHA256).
- **Key Rotation Support**: Built-in support for key IDs to manage key rotation.
- **Canonical Serialization**: Ensures consistent JSON serialization for signatures.

## Installation

```bash
pip install crypto-envelope
```

## Usage

### Signing (Cleartext Payload)

Use `EnvelopeSigner` to sign data and `EnvelopeVerifier` to verify it.

```python
from crypto_envelope import EnvelopeSigner, EnvelopeVerifier

# Signing
key = b"my-secret-signing-key"  # Can be arbitrary bytes
signer = EnvelopeSigner(active_key_id="k1", key=key)
envelope = signer.sign({"user_id": 123, "role": "admin"})

print(envelope.to_json())
# Output: {"payload": {...}, "signature": "...", "key_id": "k1", "nonce": "..."}

# Verifying
verifier = EnvelopeVerifier({"k1": key})
if verifier.verify(envelope):
    print("Signature valid!")
    print(envelope.payload)
else:
    print("Invalid signature")
```

### Encryption (Hidden Payload)

Use `EnvelopeEncrypter` to encrypt data and `EnvelopeDecryptor` to decrypt it. Requires `cryptography` library (installed by default).

```python
from crypto_envelope import EnvelopeEncrypter, EnvelopeDecryptor
from cryptography.fernet import Fernet

# Generate a secure key (32 bytes, url-safe base64)
key = Fernet.generate_key()

# Encryption
encrypter = EnvelopeEncrypter(active_key_id="k1", key=key)
enc_envelope = encrypter.encrypt({"sensitive": "data"})

print(enc_envelope.to_json())
# Output: {"token": "...", "key_id": "k1"}

# Decryption
decryptor = EnvelopeDecryptor({"k1": key})
payload = decryptor.decrypt(enc_envelope)
print(payload)
```

## Standalone Installation

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=crypto-envelope
```

## Usage

```python
import crypto_envelope
```

## Configuration

Configure active keys and key rotation via `EnvelopeSigner`, `EnvelopeVerifier`,
`EnvelopeEncrypter`, and `EnvelopeDecryptor` initialization.

## Version

Current version: **0.1.0** (see `VERSION.md`).

## Changelog

See `CHANGELOG.md` for release history.

## License

MIT License. See `LICENSE` in the repository root.
