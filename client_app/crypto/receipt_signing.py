import json, base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256

def canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def load_rsa_pubkey_pem(pem_str: str):
    return RSA.import_key(pem_str)

def verify_receipt_sig(payload: dict, sig_b64: str, rsa_pub_pem: str) -> bool:
    key = load_rsa_pubkey_pem(rsa_pub_pem)
    h = SHA256.new(canonical_bytes(payload))
    try:
        sig = base64.b64decode(sig_b64)
    except Exception:
        return False
    try:
        pss.new(key).verify(h, sig)
        return True
    except (ValueError, TypeError):
        return False
