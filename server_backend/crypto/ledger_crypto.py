"""
Ledger (block) signing using RSA-2048.
Block headers are JSON-dicts; we compute SHA-256 on the canonical JSON bytes and sign that.
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import hashlib
import json
import time

# Generate ledger RSA keys (server should persist and protect SK_ledger)
def generate_ledger_keys(key_size=2048):
    sk = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    pk = sk.public_key()
    return sk, pk

# In-memory keys (for demo). In production load from secure storage.
SK_ledger_sign, PK_ledger_sign = generate_ledger_keys()

def create_block_header(index, vote_hash, previous_hash, timestamp=None):
    if timestamp is None:
        timestamp = time.time()
    return {
        "index": int(index),
        "timestamp": float(timestamp),
        "vote_hash": str(vote_hash),
        "previous_hash": str(previous_hash)
    }

def canonical_json_bytes(data: dict) -> bytes:
    """
    Deterministic JSON bytes (sort keys) for hashing/signing.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

def sha256_of_dict(data: dict) -> bytes:
    return hashlib.sha256(canonical_json_bytes(data)).digest()

def sign_block_header(block_header: dict) -> bytes:
    """
    Sign the SHA-256 of block header using RSA-PSS + SHA256.
    Returns signature bytes.
    """
    h = sha256_of_dict(block_header)
    signature = SK_ledger_sign.sign(
        h,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return signature

def verify_block_header_signature(block_header: dict, signature: bytes, public_key_pem: bytes = None) -> bool:
    """
    Verify signature using either provided PEM public key or in-memory PK_ledger_sign.
    """
    h = sha256_of_dict(block_header)
    if public_key_pem:
        pk = serialization.load_pem_public_key(public_key_pem)
    else:
        pk = PK_ledger_sign
    try:
        pk.verify(signature, h, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        return True
    except Exception:
        return False

def export_ledger_public_key_pem():
    return PK_ledger_sign.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

def export_ledger_private_key_pem(password: bytes = None):
    encryption = serialization.NoEncryption()
    if password:
        encryption = serialization.BestAvailableEncryption(password)
    return SK_ledger_sign.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=encryption)