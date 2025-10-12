import hashlib
import json
import os

CHAIN_FILE = "blockchain.json"

def load_chain():
    if os.path.exists(CHAIN_FILE):
        with open(CHAIN_FILE, "r") as f:
            return json.load(f)
    return []

def save_chain(chain):
    with open(CHAIN_FILE, "w") as f:
        json.dump(chain, f, indent=4)

def append_block(vote_data):
    chain = load_chain()
    previous_hash = chain[-1]["hash"] if chain else "0"
    block_content = vote_data + previous_hash
    new_hash = hashlib.sha256(block_content.encode()).hexdigest()
    block = {
        "vote": vote_data, 
        "hash": new_hash, 
        "previous": previous_hash
    }
    chain.append(block)
    save_chain(chain)
