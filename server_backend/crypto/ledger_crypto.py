"""
Ledger (block) signing using RSA-2048.
Block headers are JSON-dicts; we compute SHA-256 on the canonical JSON bytes and sign that.
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import hashlib
import json
import time
from client_app.storage.localdb import store_receipt, init


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

def fetch_last_block(election_id: str, db_path="client_local.db"):
    """
    Returns the last block's index and hash for a given election,
    or (0, "0") if no blocks exist.
    """
    con = connect(db_path)
    cur = con.execute(
        "SELECT ledger_index, block_hash FROM receipts WHERE election_id=? ORDER BY ledger_index DESC LIMIT 1",
        (election_id,)
    )
    row = cur.fetchone()
    con.close()
    if row:
        return row[0], row[1]
    else:
        return 0, "0"  # Genesis block

def store_block(vote_id: str, election_id: str, block_header: dict, signature: bytes, db_path="client_local.db"):
    """
    Store a ledger block in the receipts table.
    """
    ledger_index = block_header["index"]
    block_hash = hashlib.sha256(json.dumps(block_header, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    sig_hex = signature.hex()
    store_receipt(vote_id, election_id, ledger_index, block_hash, sig_hex, db_path)