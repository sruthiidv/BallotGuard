"""
OVT (One-Time Voting Token) using RSA-2048 signatures.

- SK_server_sign: server-side RSA private key (keep secure)
- PK_server_sign: RSA public key (distribute to booths for verification)
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
import secrets

# --- Key generation (run once and persist securely) ---
def generate_rsa_keypair(key_size=2048):
    sk = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    pk = sk.public_key()
    return sk, pk

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
    signature = SK_server_sign.sign(
        token_bytes,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return signature

def verify_ovt_with_pubkey_bytes(pubkey_pem: bytes, token_bytes: bytes, signature: bytes) -> bool:
    """
    Verify signature using a provided public key PEM (useful for distributed verification).
    """
    pk = serialization.load_pem_public_key(pubkey_pem)
    try:
        pk.verify(
            signature,
            token_bytes,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def verify_ovt(token_bytes, signature_bytes):
    """
    Verify using server's in-memory public key.
    """
    try:
        PK_server_sign.verify(
            signature_bytes,
            token_bytes,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# --- Key export helpers (public) ---
def export_public_key_pem(public_key):
    """
    Returns public key in PEM bytes suitable to distribute to booth apps / verifiers.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def export_private_key_pem(private_key, password: bytes = None):
    """
    Export private key in PEM (encrypted if password provided). Use only if you know
    how to store securely (prefer a secret manager).
    """
    encryption = serialization.NoEncryption()
    if password:
        encryption = serialization.BestAvailableEncryption(password)
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption
    )
