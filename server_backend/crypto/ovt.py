"""
OVT (One-Time Voting Token) using RSA-2048 signatures.

- SK_server_sign: server-side RSA private key (keep secure)
- PK_server_sign: RSA public key (distribute to booths for verification)
"""

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
import secrets

# --- Key generation (run once and persist securely) ---
def generate_rsa_keypair(key_size=2048):
    key = RSA.generate(key_size)
    return key, key.publickey()

# For convenience, generate in-memory keys (in production load from secure storage)
SK_server_sign, PK_server_sign = generate_rsa_keypair()

# --- OVT functions ---
def generate_ovt(length=16):
    """
    Create a random one-time token (bytes).
    """
    return secrets.token_hex(length).encode()

def sign_ovt(token_bytes):
    """
    Sign a token (bytes) with server private RSA key (PSS+SHA256).
    Returns signature bytes.
    """
    h = SHA256.new(token_bytes)
    signer = pss.new(SK_server_sign)
    return signer.sign(h)

def verify_ovt_with_pubkey_bytes(pubkey_pem: bytes, token_bytes: bytes, signature: bytes) -> bool:
    """
    Verify signature using a provided public key PEM (useful for distributed verification).
    """
    try:
        pk = RSA.import_key(pubkey_pem)
        h = SHA256.new(token_bytes)
        verifier = pss.new(pk)
        verifier.verify(h, signature)
        return True
    except Exception:
        return False

def verify_ovt(token_bytes, signature_bytes):
    """
    Verify using server's in-memory public key.
    """
    try:
        h = SHA256.new(token_bytes)
        verifier = pss.new(PK_server_sign)
        verifier.verify(h, signature_bytes)
        return True
    except Exception:
        return False

# --- Key export helpers (public) ---
def export_public_key_pem(public_key):
    """
    Returns public key in PEM bytes suitable to distribute to booth apps / verifiers.
    """
    return public_key.export_key('PEM')

def export_private_key_pem(private_key, password: bytes = None):
    """
    Export private key in PEM (encrypted if password provided). Use only if you know
    how to store securely (prefer a secret manager).
    """
    if password:
        return private_key.export_key('PEM', passphrase=password)
    return private_key.export_key('PEM')