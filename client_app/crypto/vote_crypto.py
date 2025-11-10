import base64
import json
import uuid
import hashlib
import sys
import os
from server_backend.crypto.sha_utils import compute_sha256_hex, compute_sha256_bytes

# Add parent directory for imports
sys.path.append(os.path.dirname(__file__))
from paillier import build_public_key_from_n, encrypt_multicandidate_vote  # ✅ fixed imports

def prepare_vote_data(vote_id, election_id, candidate_id, candidate_index=None, total_candidates=None, ovt=None, n_int=None):
    """Prepare encrypted vote data for submission"""

    if candidate_index is not None and total_candidates is not None and n_int is not None:
        # ✅ Real Paillier encryption using one-hot encoding
        public_key = build_public_key_from_n(n_int)
        encrypted_vector = encrypt_multicandidate_vote(candidate_index, total_candidates, public_key)
        ciphertext = [str(e.ciphertext()) for e in encrypted_vector]
        try:
            print(f"DEBUG: Encryption complete (Paillier). vote_id={vote_id}, election_id={election_id}, candidate_id={candidate_id}, vector_len={len(ciphertext)}")
        except Exception:
            pass
    else:
        # fallback
        ciphertext = f"encrypted_vote_for_{candidate_id}"
        try:
            print(f" vote_id={vote_id}, election_id={election_id}, candidate_id={candidate_id}")
        except Exception:
            pass

    # Generate client-side integrity hash
    vote_content = f"{vote_id}{election_id}{candidate_id}"
    client_hash = compute_sha256_hex(vote_content)


    # --- OVT handling ---
    ovt_payload = ovt if ovt else {}

    return {
        "vote_id": vote_id,
        "election_id": election_id,
        "candidate_id": candidate_id,
        "ciphertext": ciphertext,
        "client_hash": client_hash,
        "ovt": ovt_payload
    }

def generate_vote_id():
    """Generate a unique vote ID"""
    return str(uuid.uuid4())

def verify_vote_receipt(vote_data, receipt_data):
    """Verify that the vote receipt matches the submitted data"""
    return (
        receipt_data.get("vote_id") == vote_data.get("vote_id") and
        receipt_data.get("election_id") == vote_data.get("election_id")
    )
