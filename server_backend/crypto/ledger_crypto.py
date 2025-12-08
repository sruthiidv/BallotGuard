"""
Ledger (block) signing using RSA-PSS (aligned with server.py implementation).
Block headers are JSON-dicts; we compute SHA-256 on the canonical JSON bytes and sign that.

This module provides test-compatible wrappers around the server's signing functions.
The actual production signing uses the server's RSA_SK key from server_config.py.
"""

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
import hashlib
import json
import time
import base64
import os
import sys

# Add server directory to path to import server_config
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

try:
    from server_config import RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM
    # Use the same RSA key that server.py uses for signing
    RSA_SK = RSA.import_key(RECEIPT_RSA_PRIV_PEM)
    RSA_PK = RSA.import_key(RECEIPT_RSA_PUB_PEM)
    print("[LEDGER_CRYPTO] ✓ Using production RSA keys from server_config")
except ImportError:
    # Fallback for tests that don't have server_config
    print("[LEDGER_CRYPTO] ⚠ server_config not found, generating test keys")
    RSA_SK = RSA.generate(3072)
    RSA_PK = RSA_SK.publickey()


def create_block_header(index, vote_hash, previous_hash, timestamp=None):
    """Create a blockchain block header dictionary"""
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
    Must match server.py's JSON serialization format exactly.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()


def sha256_of_dict(data: dict) -> bytes:
    """Compute SHA-256 hash of a dictionary (deterministic JSON)"""
    return hashlib.sha256(canonical_json_bytes(data)).digest()


def sign_block_header(block_header: dict) -> bytes:
    """
    Sign the SHA-256 of block header using RSA-PSS + SHA256.
    Returns signature bytes (matching server.py implementation).
    
    Note: server.py returns base64 string, but tests expect bytes.
    This function returns raw bytes for test compatibility.
    """
    msg_bytes = canonical_json_bytes(block_header)
    h = SHA256.new(msg_bytes)
    signer = pss.new(RSA_SK)
    signature = signer.sign(h)
    return signature


def sign_block_header_base64(block_header: dict) -> str:
    """
    Sign block header and return base64 string (server.py compatible).
    This matches the format stored in the database.
    """
    signature = sign_block_header(block_header)
    return base64.b64encode(signature).decode()


def verify_block_header_signature(block_header: dict, signature: bytes, public_key_pem: bytes = None) -> bool:
    """
    Verify signature using either provided PEM public key or default RSA_PK.
    Accepts signature as bytes.
    """
    msg_bytes = canonical_json_bytes(block_header)
    h = SHA256.new(msg_bytes)
    
    if public_key_pem:
        pk = RSA.import_key(public_key_pem)
    else:
        pk = RSA_PK
    
    try:
        verifier = pss.new(pk)
        verifier.verify(h, signature)
        return True
    except Exception:
        return False


def verify_block_signature_base64(block_header: dict, signature_b64: str) -> bool:
    """
    Verify signature from base64 string (server.py/database compatible).
    This matches the format retrieved from the database.
    """
    try:
        signature = base64.b64decode(signature_b64)
        return verify_block_header_signature(block_header, signature)
    except Exception:
        return False


def export_ledger_public_key_pem() -> bytes:
    """Export the public key as PEM bytes"""
    return RSA_PK.export_key('PEM')


def export_ledger_private_key_pem(password: bytes = None) -> bytes:
    """Export the private key as PEM bytes (optionally encrypted)"""
    if password:
        return RSA_SK.export_key('PEM', passphrase=password)
    return RSA_SK.export_key('PEM')