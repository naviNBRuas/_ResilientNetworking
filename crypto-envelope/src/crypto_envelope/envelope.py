from __future__ import annotations

import base64
import hmac
import json
import os
from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Any, Dict, Optional, Union

try:
    from cryptography.fernet import Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


def _canonical_json_bytes(data: Any) -> bytes:
    """Produces a canonical JSON byte string (sorted keys, no spaces)."""
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')


@dataclass
class Envelope:
    """
    Represents a signed message with cleartext payload.
    """
    payload: Dict[str, Any]
    signature: str
    key_id: str
    nonce: str

    def to_json(self) -> str:
        """Serializes the envelope to a JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> Envelope:
        """Deserializes an envelope from a JSON string."""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class EncryptedEnvelope:
    """
    Represents an encrypted message (authenticated encryption).
    """
    token: str
    key_id: str

    def to_json(self) -> str:
        """Serializes the envelope to a JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> EncryptedEnvelope:
        """Deserializes an envelope from a JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class EnvelopeVerifier:
    """
    Verifies signed Envelopes using a keyring.
    """
    def __init__(self, keys: Dict[str, bytes]):
        self.keys = keys

    def verify(self, envelope: Envelope) -> bool:
        """
        Verifies the signature of the envelope.
        Returns True if valid, False otherwise.
        """
        key = self.keys.get(envelope.key_id)
        if not key:
            return False
        try:
            expected = self._compute_signature(envelope.payload, key, envelope.nonce)
            return hmac.compare_digest(expected, envelope.signature)
        except Exception:
            return False

    @staticmethod
    def _compute_signature(payload: Dict[str, Any], key: bytes, nonce: str) -> str:
        # payload and nonce are signed
        message = _canonical_json_bytes({"payload": payload, "nonce": nonce})
        return base64.b64encode(hmac.new(key, message, sha256).digest()).decode()


class EnvelopeSigner:
    """
    Creates signed Envelopes.
    """
    def __init__(self, active_key_id: str, key: bytes):
        self.active_key_id = active_key_id
        self.key = key

    def sign(self, payload: Dict[str, Any]) -> Envelope:
        """
        Signs the payload and returns an Envelope.
        """
        nonce = base64.b64encode(os.urandom(12)).decode()
        signature = EnvelopeVerifier._compute_signature(payload, self.key, nonce)
        return Envelope(
            payload=payload,
            signature=signature,
            key_id=self.active_key_id,
            nonce=nonce
        )

    # Alias for backward compatibility (conceptually)
    seal = sign


# Deprecated alias
EnvelopeCipher = EnvelopeSigner


class EnvelopeEncrypter:
    """
    Encrypts payloads using Fernet (AES-128-CBC + HMAC-SHA256).
    """
    def __init__(self, active_key_id: str, key: bytes):
        if not _CRYPTO_AVAILABLE:
            raise ImportError("cryptography library is required for encryption")
        self.active_key_id = active_key_id
        # Ensure key is valid for Fernet (32 bytes url-safe base64)
        # If user passes raw bytes, Fernet(key) will validate it.
        self.fernet = Fernet(key)

    def encrypt(self, payload: Dict[str, Any]) -> EncryptedEnvelope:
        """
        Encrypts the payload and returns an EncryptedEnvelope.
        """
        data = _canonical_json_bytes(payload)
        token = self.fernet.encrypt(data).decode('ascii')
        return EncryptedEnvelope(token=token, key_id=self.active_key_id)


class EnvelopeDecryptor:
    """
    Decrypts EncryptedEnvelopes using a keyring.
    """
    def __init__(self, keys: Dict[str, bytes]):
        if not _CRYPTO_AVAILABLE:
            raise ImportError("cryptography library is required for encryption")
        self.keys = keys

    def decrypt(self, envelope: EncryptedEnvelope) -> Dict[str, Any]:
        """
        Decrypts the envelope. Raises InvalidToken (from cryptography) or ValueError on failure.
        """
        key = self.keys.get(envelope.key_id)
        if not key:
            raise ValueError(f"Unknown key ID: {envelope.key_id}")
        
        f = Fernet(key)
        data = f.decrypt(envelope.token.encode('ascii'))
        return json.loads(data.decode('utf-8'))