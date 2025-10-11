import json
import uuid
import hashlib
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(__file__))
from paillier import load_public_key, encrypt_one_hot

def prepare_vote_data(vote_id, election_id, candidate_id, candidate_index=None, total_candidates=None, ovt=None):
    """Prepare encrypted vote data for submission"""
    
    # For now, use mock encryption - in production, use Paillier encryption
    if candidate_index is not None and total_candidates is not None:
        # Use Paillier encryption for one-hot encoding
        # This would require loading the public key from server
        # pubkey = load_public_key(n_int)  # Would get n from server
        # ciphertext = encrypt_one_hot(candidate_index, total_candidates, pubkey)
        
        # Mock encryption for now
        ciphertext = f"encrypted_vote_for_candidate_{candidate_index}_of_{total_candidates}"
    else:
        # Simple mock encryption
        ciphertext = f"encrypted_vote_for_{candidate_id}"
    
    # Generate client hash for integrity
    vote_content = f"{vote_id}{election_id}{candidate_id}"
    client_hash = hashlib.sha256(vote_content.encode()).hexdigest()
    
    return {
        "vote_id": vote_id,
        "election_id": election_id,
        "candidate_id": candidate_id,
        "ciphertext": ciphertext,
        "client_hash": client_hash,
        "ovt": ovt or {}
    }

def generate_vote_id():
    """Generate a unique vote ID"""
    return str(uuid.uuid4())

def verify_vote_receipt(vote_data, receipt_data):
    """Verify that the vote receipt matches the submitted data"""
    # In production, this would verify cryptographic signatures
    # For now, just check basic consistency
    return (
        receipt_data.get("vote_id") == vote_data.get("vote_id") and
        receipt_data.get("election_id") == vote_data.get("election_id")
    )