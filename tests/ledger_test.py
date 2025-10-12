from server_backend.crypto.ledger_crypto import (
    create_block_header,
    sign_block_header,
    verify_block_header_signature
)

# --- Step 1: Create a block header ---
index = 1
vote_hash = "abcdef123456"  # mock vote hash
previous_hash = "000000000000"
block_header = create_block_header(index, vote_hash, previous_hash)
print("Block header:", block_header)

# --- Step 2: Sign the block header ---
signature = sign_block_header(block_header)
print("Signature (hex):", signature.hex())

# --- Step 3: Verify the signature ---
is_valid = verify_block_header_signature(block_header, signature)
print("Verification result:", is_valid)  # Should be True
