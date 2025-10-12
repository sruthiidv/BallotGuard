"""
Client-side Paillier helpers.

Clients only need the Paillier public key (n). We construct a PaillierPublicKey
from the integer n using phe.PaillierPublicKey(n).
"""

from phe import paillier

def build_public_key_from_n(n_int):
    """
    Construct a PaillierPublicKey (phe) from integer n received from server.
    """
    return paillier.PaillierPublicKey(n_int)

def paillier_encrypt(public_key, vote_value: int):
    """
    Encrypt a single integer vote using the provided PaillierPublicKey.
    Returns phe.EncryptedNumber.
    """
    return public_key.encrypt(vote_value)

def encrypt_multicandidate_vote(vote_index, num_candidates, public_key):
    """
    One-hot encode and encrypt each entry.
    Returns list of phe.EncryptedNumber objects.
    """
    vote_vector = [0] * num_candidates
    vote_vector[vote_index] = 1
    return [paillier_encrypt(public_key, v) for v in vote_vector]

def serialize_encrypted_vector(encrypted_vector):
    """
    Convert list of EncryptedNumber to list of strings (ciphertext ints)
    for JSON transmission.
    """
    return [str(e.ciphertext()) for e in encrypted_vector]

def deserialize_encrypted_vector(public_key, serialized_vector):
    """
    Build EncryptedNumber objects back from string list (client-side seldom needed).
    """
    return [paillier.EncryptedNumber(public_key, int(s)) for s in serialized_vector]