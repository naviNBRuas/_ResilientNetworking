import json
import pytest
from cryptography.fernet import Fernet
from crypto_envelope import (
    EnvelopeSigner, 
    EnvelopeVerifier, 
    EnvelopeEncrypter, 
    EnvelopeDecryptor, 
    Envelope, 
    EncryptedEnvelope
)

# --- Signing Tests ---

def test_envelope_sign_and_verify():
    key = b"secret-key-must-be-bytes"
    signer = EnvelopeSigner(active_key_id="k1", key=key)
    payload = {"msg": "hello", "val": 123}
    
    env = signer.sign(payload)
    
    assert env.key_id == "k1"
    assert env.payload == payload
    assert env.signature is not None
    assert env.nonce is not None
    
    verifier = EnvelopeVerifier({"k1": key})
    assert verifier.verify(env) is True

def test_envelope_verify_fails_wrong_key():
    key1 = b"secret-key-1"
    key2 = b"secret-key-2"
    
    signer = EnvelopeSigner(active_key_id="k1", key=key1)
    env = signer.sign({"msg": "hi"})
    
    # Verify with wrong key associated with k1
    verifier = EnvelopeVerifier({"k1": key2})
    assert verifier.verify(env) is False

def test_envelope_verify_fails_unknown_key_id():
    key = b"secret-key"
    signer = EnvelopeSigner(active_key_id="k1", key=key)
    env = signer.sign({"msg": "hi"})
    
    verifier = EnvelopeVerifier({"k2": key})
    assert verifier.verify(env) is False

def test_envelope_verify_fails_tampered_payload():
    key = b"secret-key"
    signer = EnvelopeSigner(active_key_id="k1", key=key)
    env = signer.sign({"msg": "valid"})
    
    # Tamper payload
    env.payload["msg"] = "evil"
    
    verifier = EnvelopeVerifier({"k1": key})
    assert verifier.verify(env) is False

def test_envelope_serialization():
    key = b"secret-key"
    signer = EnvelopeSigner(active_key_id="k1", key=key)
    env = signer.sign({"foo": "bar"})
    
    json_str = env.to_json()
    loaded_env = Envelope.from_json(json_str)
    
    assert loaded_env == env

# --- Encryption Tests ---

def test_encryption_decryption():
    key = Fernet.generate_key()
    encrypter = EnvelopeEncrypter(active_key_id="k1", key=key)
    payload = {"secret": "plans", "code": 42}
    
    enc_env = encrypter.encrypt(payload)
    
    assert isinstance(enc_env, EncryptedEnvelope)
    assert enc_env.key_id == "k1"
    assert enc_env.token is not None
    
    decryptor = EnvelopeDecryptor({"k1": key})
    decrypted_payload = decryptor.decrypt(enc_env)
    
    assert decrypted_payload == payload

def test_decryption_fails_wrong_key():
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    
    encrypter = EnvelopeEncrypter(active_key_id="k1", key=key1)
    enc_env = encrypter.encrypt({"msg": "hidden"})
    
    decryptor = EnvelopeDecryptor({"k1": key2})
    
    with pytest.raises(Exception): # InvalidToken
        decryptor.decrypt(enc_env)

def test_decryption_fails_unknown_key_id():
    key = Fernet.generate_key()
    encrypter = EnvelopeEncrypter(active_key_id="k1", key=key)
    enc_env = encrypter.encrypt({"msg": "hidden"})
    
    decryptor = EnvelopeDecryptor({"k2": key})
    
    with pytest.raises(ValueError, match="Unknown key ID"):
        decryptor.decrypt(enc_env)

def test_encrypted_envelope_serialization():
    key = Fernet.generate_key()
    encrypter = EnvelopeEncrypter(active_key_id="k1", key=key)
    enc_env = encrypter.encrypt({"foo": "bar"})
    
    json_str = enc_env.to_json()
    loaded_env = EncryptedEnvelope.from_json(json_str)
    
    assert loaded_env == enc_env