"""
Server-side Paillier utilities: key generation, serialization and tallying.
Uses phe (Python Paillier).
"""

from phe import paillier
import json

def generate_paillier_keys():
    """
    Generate Paillier keypair. Return (public_key, private_key).
    """
    public_key, private_key = paillier.generate_paillier_keypair()
    return public_key, private_key

def public_key_to_dict(public_key):
    """
    Serialize Paillier public key to a simple dict to send to clients.
    The phe PaillierPublicKey exposes attribute 'n'.
    """
    return {"n": public_key.n}

def public_key_from_dict(d):
    """
    Deserialize Paillier public key from dict with integer 'n'.
    """
    return paillier.PaillierPublicKey(d["n"])

def paillier_tally(private_key, encrypted_votes):
    """
    Homomorphically sum a list of EncryptedNumber objects (all for same pubkey)
    and decrypt the result. Returns integer total.
    If encrypted_votes is a list of EncryptedNumber, returns private_key.decrypt(sum).
    """
    if not encrypted_votes:
        return 0
    total_enc = encrypted_votes[0]
    for enc in encrypted_votes[1:]:
        total_enc += enc
    return private_key.decrypt(total_enc)

def paillier_decrypt(private_key, encrypted_number):
    """
    Decrypt a single EncryptedNumber.
    """
    return private_key.decrypt(encrypted_number)

def save_paillier_keys_to_file(public_key, private_key, pub_path, priv_path):
    """
    Save keys to disk in JSON (public.n and private serialized).
    WARNING: store private key securely (file permissions, secret manager).
    We'll serialize private_key.p as repr of private_key (phe object has p,q).
    """
    with open(pub_path, "w") as f:
        json.dump({"n": public_key.n}, f)
    # private key internals: p and q (integers)
    with open(priv_path, "w") as f:
        json.dump({"p": private_key.p, "q": private_key.q}, f)

def load_paillier_keys_from_file(pub_path, priv_path):
    import json
    from phe import paillier
    with open(pub_path, "r") as f:
        pd = json.load(f)
    with open(priv_path, "r") as f:
        kd = json.load(f)
    pub = paillier.PaillierPublicKey(pd["n"])
    priv = paillier.PaillierPrivateKey(pub, kd["p"], kd["q"])
    return pub, priv
