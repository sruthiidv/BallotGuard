from server_backend.crypto import sha_utils

data = "Hello BallotGuard!"
hash_hex = sha_utils.compute_sha256_hex(data)
hash_bytes = sha_utils.compute_sha256_bytes(data)

print("SHA256 hex:", hash_hex)
print("SHA256 bytes:", hash_bytes)
