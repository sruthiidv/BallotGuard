from client_app.crypto.vote_crypto import prepare_vote_data, generate_vote_id
from client_app.crypto.paillier import build_public_key_from_n, encrypt_multicandidate_vote
from server_backend.blockchain.blockchain import Blockchain
from server_backend.crypto import ledger_crypto
import hashlib

# Example election
n_int = 2357
total_candidates = 3

blockchain = Blockchain()

# Simulate 3 votes
for candidate_index in range(3):
    vote_id = generate_vote_id()
    vote_payload = prepare_vote_data(vote_id, "election123", candidate_index, candidate_index, total_candidates, n_int=n_int)
    
    vote_json = str(vote_payload["ciphertext"])
    vote_hash = hashlib.sha256(vote_json.encode()).hexdigest()
    
    # Correct index for new block
    new_index = len(blockchain.chain)
    
    header = ledger_crypto.create_block_header(index=new_index, vote_hash=vote_hash, previous_hash=blockchain.last_hash())
    signature = ledger_crypto.sign_block_header(header)
    
    blockchain.add_block(vote_hash, header_signature=signature)


# Print blockchain
for b in blockchain.to_list_of_dicts():
    print(b)
