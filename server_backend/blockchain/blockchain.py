"""
Lightweight append-only blockchain ledger to store vote hashes.
Each block stores: index, timestamp, vote_hash, previous_hash, hash.
The signing of the block header is done by ledger_crypto.sign_block_header and stored alongside block.
"""

import hashlib
import time
import json

class Block:
    def __init__(self, index, timestamp, vote_hash, previous_hash, header_signature=None):
        self.index = int(index)
        self.timestamp = float(timestamp)
        self.vote_hash = vote_hash
        self.previous_hash = previous_hash
        self.header_signature = header_signature  # bytes hex string or None
        self.hash = self.compute_hash()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "vote_hash": self.vote_hash,
            "previous_hash": self.previous_hash,
            "header_signature": self.header_signature.hex() if isinstance(self.header_signature, (bytes, bytearray)) else self.header_signature,
            "hash": self.hash
        }

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "vote_hash": self.vote_hash,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, time.time(), "GENESIS", "0", header_signature=None)
        self.chain.append(genesis)

    def add_block(self, vote_hash, header_signature=None):
        last = self.chain[-1]
        new_block = Block(last.index + 1, time.time(), vote_hash, last.hash, header_signature=header_signature)
        self.chain.append(new_block)
        return new_block

    def last_hash(self):
        return self.chain[-1].hash

    def to_list_of_dicts(self):
        return [b.to_dict() for b in self.chain]
