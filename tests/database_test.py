from client_app.storage.localdb import (
    init, store_ovt, is_ovt_used, store_vote, store_receipt,
    fetch_last_receipt, mark_ovt_used
)
from client_app.crypto.vote_crypto import prepare_vote_data, generate_vote_id
from server_backend.crypto.ovt import generate_ovt, sign_ovt, export_public_key_pem
from server_backend.crypto.sha_utils import compute_sha256_hex
from server_backend.crypto.ledger_crypto import create_block_header, sign_block_header
import time

DB_PATH = "client_local.db"

# --- Step 1: Initialize DB ---
init(DB_PATH)
print("Database initialized with tables.")

# --- Step 2: Generate a dynamic OVT token ---
ovt_token_bytes = generate_ovt()               # random token bytes
ovt_signature = sign_ovt(ovt_token_bytes)      # sign the token
ovt_token_str = ovt_token_bytes.hex()          # store as hex in DB
election_id = "TEST_ELECTION"

store_ovt(ovt_token_str, election_id, DB_PATH)
print(f"OVT stored dynamically: {ovt_token_str}, used? {is_ovt_used(ovt_token_str, DB_PATH)}")

# --- Step 3: Generate a real vote ---
vote_id = generate_vote_id()
candidate_id = "CAND1"  # dynamically can be any candidate chosen
# Example: simulate encrypted vote (you can pass real params if you have PK)
vote_data = prepare_vote_data(
    vote_id=vote_id,
    election_id=election_id,
    candidate_id=candidate_id,
    ovt={"token": ovt_token_str, "signature": ovt_signature.hex()}
)

store_vote(vote_id, election_id, str(vote_data), ovt_token_str, DB_PATH)
print(f"Vote stored dynamically: {vote_id}")

# --- Step 4: Generate ledger receipt ---
last_index, last_hash = fetch_last_receipt(election_id, DB_PATH)
vote_hash = compute_sha256_hex(str(vote_data))  # dynamically hashed
block_header = create_block_header(last_index + 1, vote_hash, last_hash)
signature_bytes = sign_block_header(block_header)

store_receipt(vote_id, election_id, block_header["index"], vote_hash, signature_bytes.hex(), DB_PATH)
print(f"Receipt stored for vote {vote_id}")

# --- Step 5: Mark OVT used ---
mark_ovt_used(ovt_token_str, DB_PATH)
print(f"OVT used after marking? {is_ovt_used(ovt_token_str, DB_PATH)}")
