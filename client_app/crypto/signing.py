import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

def canonical_json_bytes(obj: dict) -> bytes:
    """
    Convert a dict to canonical JSON bytes (sorted keys, compact separators)
    for consistent signing/verification.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def verify_rsa_signature(message_obj: dict, sig_b64: str, pubkey_pem_b64: str) -> bool:
    """
    Verify an RSA-PSS signature on a JSON object.

    Parameters:
    - message_obj: dict to verify
    - sig_b64: base64-encoded signature
    - pubkey_pem_b64: base64-encoded PEM of RSA public key

    Returns True if valid, False otherwise.
    """
    try:
        # Decode base64 PEM and signature
        pubkey_pem = base64.b64decode(pubkey_pem_b64)
        signature = base64.b64decode(sig_b64)
        
        # Load RSA public key
        pk = serialization.load_pem_public_key(pubkey_pem)
        
        # Canonical JSON bytes
        msg_bytes = canonical_json_bytes(message_obj)
        
        # Verify using RSA-PSS + SHA256
        pk.verify(
            signature,
            msg_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
