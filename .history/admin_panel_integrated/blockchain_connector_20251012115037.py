import sys
import os
import json
import time

# Add server_backend to path to import blockchain modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server_backend'))

try:
    from blockchain.blockchain import Blockchain, Block
    from blockchain.ledger import load_chain, save_chain, append_block
    from crypto.sha_utils import compute_sha256_hex
    BLOCKCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Blockchain modules not available: {e}")
    print("📝 Running in simulation mode")
    BLOCKCHAIN_AVAILABLE = False

class BlockchainConnector:
    def __init__(self):
        self.blockchain = None
        self.mock_votes = []  # Fallback for demo
        self.chain_broken = False
        self.original_chain_state = None
        
        if BLOCKCHAIN_AVAILABLE:
            try:
                self.blockchain = Blockchain()
                # Save original chain state for integrity verification
                self.original_chain_state = self.get_chain_hash()
                print("✅ Blockchain initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize blockchain: {e}")
                print("📝 Using mock blockchain for demo")
                self.blockchain = None
        
        # Initialize with some demo data
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize with demo votes for presentation"""
        demo_votes = [
            {"candidate": "Candidate A", "voter_id": "voter_001", "timestamp": time.time() - 3600},
            {"candidate": "Candidate B", "voter_id": "voter_002", "timestamp": time.time() - 3500},
            {"candidate": "Candidate A", "voter_id": "voter_003", "timestamp": time.time() - 3400},
            {"candidate": "Candidate C", "voter_id": "voter_004", "timestamp": time.time() - 3300},
            {"candidate": "Candidate B", "voter_id": "voter_005", "timestamp": time.time() - 3200},
            {"candidate": "Candidate A", "voter_id": "voter_006", "timestamp": time.time() - 3100},
            {"candidate": "Candidate C", "voter_id": "voter_007", "timestamp": time.time() - 3000},
        ]
        
        for vote in demo_votes:
            self.add_vote_to_blockchain(vote)
        
        # Update original chain state after demo data
        if self.blockchain:
            self.original_chain_state = self.get_chain_hash()
    
    def get_chain_hash(self):
        """Get hash of entire blockchain for integrity verification"""
        try:
            if self.blockchain:
                chain_data = ""
                for block in self.blockchain.chain:
                    chain_data += f"{block.index}{block.timestamp}{block.vote_hash}{block.previous_hash}{block.hash}"
                return compute_sha256_hex(chain_data)
            return "mock_chain_hash"
        except Exception as e:
            return f"error_{str(e)}"
    
    def verify_chain_integrity(self):
        """Verify if blockchain chain is intact"""
        try:
            current_hash = self.get_chain_hash()
            return current_hash == self.original_chain_state
        except:
            return False
    
    def break_chain_on_admin_modification(self, modification_type):
        """Simulate chain break when admin tries to modify blockchain"""
        self.chain_broken = True
        
        # Log the violation but keep values intact
        violation_details = {
            "timestamp": time.time(),
            "modification_type": modification_type,
            "chain_status": "BROKEN",
            "integrity_violation": True,
            "admin
