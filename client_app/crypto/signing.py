import json, base64
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

def canonical_json_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def verify_ed25519_signature(message_obj: dict, sig_b64: str, pubkey_b64: str) -> bool:
    vk = VerifyKey(base64.b64decode(pubkey_b64))
    msg = canonical_json_bytes(message_obj)
    sig = base64.b64decode(sig_b64)
    try:
        vk.verify(msg, sig)
        return True
    except BadSignatureError:
        return False
