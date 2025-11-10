from phe import paillier
from client_app.crypto.paillier import build_public_key_from_n, encrypt_multicandidate_vote

# Server side: generate keypair
pub, priv = paillier.generate_paillier_keypair()
n_int = pub.n

# Client side: encrypt vote
client_pub = build_public_key_from_n(n_int)
encrypted_votes = encrypt_multicandidate_vote(1, 3, client_pub)

# Server side: decrypt
decrypted_votes = [priv.decrypt(v) for v in encrypted_votes]
print("Decrypted votes:", decrypted_votes)  # Should be [0,1,0]
