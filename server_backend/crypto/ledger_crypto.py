"""
Ledger (block) signing using RSA-2048.
Block headers are JSON-dicts; we compute SHA-256 on the canonical JSON bytes and sign that.
"""

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
import hashlib
import json
import time
from client_app.storage.localdb import store_receipt, init, connect
import os


# Generate ledger RSA keys (server should persist and protect SK_ledger)
def generate_ledger_keys(key_size=2048):
    key = RSA.generate(key_size)
    return key, key.publickey()

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
    msg_bytes = canonical_json_bytes(block_header)
    h = SHA256.new(msg_bytes)
    signer = pss.new(SK_ledger_sign)
    signature = signer.sign(h)
    return signature

def verify_block_header_signature(block_header: dict, signature: bytes, public_key_pem: bytes = None) -> bool:
    """
    Verify signature using either provided PEM public key or in-memory PK_ledger_sign.
    """
    msg_bytes = canonical_json_bytes(block_header)
    h = SHA256.new(msg_bytes)
    if public_key_pem:
        pk = RSA.import_key(public_key_pem)
    else:
        pk = PK_ledger_sign
    try:
        verifier = pss.new(pk)
        verifier.verify(h, signature)
        return True
    except Exception:
        return False

def export_ledger_public_key_pem():
    return PK_ledger_sign.export_key('PEM')

def export_ledger_private_key_pem(password: bytes = None):
    if password:
        return SK_ledger_sign.export_key('PEM', passphrase=password)
    return SK_ledger_sign.export_key('PEM')

def fetch_last_block(election_id: str, db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), '../../database/server_ledger.db')
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

def store_block(vote_id: str, election_id: str, block_header: dict, signature: bytes, db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), '../../database/server_ledger.db')
    """
    Store a ledger block in the receipts table.
    """
    ledger_index = block_header["index"]
    block_hash = hashlib.sha256(json.dumps(block_header, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    sig_hex = signature.hex()
    store_receipt(vote_id, election_id, ledger_index, block_hash, sig_hex, db_path)