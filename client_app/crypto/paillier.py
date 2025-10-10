from phe import paillier

def load_public_key(n_int: int, g_int: int | None = None) -> paillier.PaillierPublicKey:
    # phe uses n; g is effectively n+1 internally for standard Paillier
    return paillier.PaillierPublicKey(n_int)

def encrypt_one_hot(index: int, k: int, pubkey: paillier.PaillierPublicKey) -> list[str]:
    """
    Encrypt a one-hot vector of length k with 1 at 'index'.
    Returns hex strings for ciphertexts (raw integers mod n^2).
    """
    out_hex = []
    for i in range(k):
        m = 1 if i == index else 0
        c = pubkey.encrypt(m)  # EncryptedNumber
        out_hex.append(format(c.ciphertext(), 'x'))
    return out_hex
