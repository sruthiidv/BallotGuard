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
            "admin_attempted_modification": True
        }
        
        return violation_details
    
    def get_vote_tally(self):
        """Get current vote tally from blockchain"""
        try:
            tally = {"Candidate A": 0, "Candidate B": 0, "Candidate C": 0}
            total_votes = 0
            
            # Get actual tally from mock votes
            for vote in self.mock_votes:
                if vote["candidate"] in tally:
                    tally[vote["candidate"]] += 1
                    total_votes += 1
            
            return {
                "candidates": [
                    {"id": "A", "name": "Candidate A", "votes": tally["Candidate A"]},
                    {"id": "B", "name": "Candidate B", "votes": tally["Candidate B"]},
                    {"id": "C", "name": "Candidate C", "votes": tally["Candidate C"]}
                ],
                "total_votes": total_votes,
                "blockchain_blocks": len(self.blockchain.chain) if self.blockchain else len(self.mock_votes),
                "chain_broken": self.chain_broken,
                "integrity_verified": self.verify_chain_integrity()
            }
            
        except Exception as e:
            print(f"⚠️ Error getting vote tally: {e}")
            return {
                "candidates": [
                    {"id": "A", "name": "Candidate A", "votes": 0},
                    {"id": "B", "name": "Candidate B", "votes": 0},
                    {"id": "C", "name": "Candidate C", "votes": 0}
                ],
                "total_votes": 0,
                "blockchain_blocks": 0,
                "chain_broken": True,
                "integrity_verified": False
            }
    
    def get_blockchain_info(self):
        """Get blockchain statistics"""
        try:
            if self.blockchain:
                return {
                    "total_blocks": len(self.blockchain.chain),
                    "genesis_hash": self.blockchain.chain[0].hash if self.blockchain.chain else "N/A",
                    "latest_hash": self.blockchain.chain[-1].hash if self.blockchain.chain else "N/A",
                    "blockchain_file_exists": os.path.exists("blockchain.json"),
                    "chain_broken": self.chain_broken,
                    "integrity_verified": self.verify_chain_integrity()
                }
            else:
                return {
                    "total_blocks": len(self.mock_votes),
                    "blockchain_file_exists": True,
                    "mode": "mock",
                    "chain_broken": self.chain_broken,
                    "integrity_verified": not self.chain_broken
                }
        except Exception as e:
            return {
                "error": str(e),
                "chain_broken": True,
                "integrity_verified": False
            }
    
    def get_recent_blocks(self, limit=10):
        """Get recent blockchain blocks for display"""
        try:
            if self.blockchain:
                recent_blocks = []
                blocks_to_show = self.blockchain.chain[-limit:] if len(self.blockchain.chain) > limit else self.blockchain.chain
                
                for block in blocks_to_show:
                    recent_blocks.append({
                        "index": block.index,
                        "timestamp": time.strftime("%H:%M:%S", time.localtime(block.timestamp)),
                        "hash": block.hash[:16] + "..." if not self.chain_broken else "COMPROMISED",
                        "previous_hash": block.previous_hash[:16] + "..." if block.previous_hash != "0" else "GENESIS",
                        "status": "COMPROMISED" if self.chain_broken else "VALID"
                    })
                
                return recent_blocks
            else:
                # Mock recent blocks
                return [
                    {
                        "index": i, 
                        "timestamp": time.strftime("%H:%M:%S"), 
                        "hash": f"mock_hash_{i}..." if not self.chain_broken else "COMPROMISED",
                        "previous_hash": f"prev_{i-1}..." if i > 1 else "GENESIS",
                        "status": "COMPROMISED" if self.chain_broken else "VALID"
                    }
                    for i in range(max(1, len(self.mock_votes) - limit + 1), len(self.mock_votes) + 1)
                ]
                
        except Exception as e:
            print(f"Error getting recent blocks: {e}")
            return []
    
    def modify_vote_count(self, candidate, new_count):
        """Attempt to modify vote count (admin function - will break chain)"""
        violation = self.break_chain_on_admin_modification("VOTE_COUNT_MODIFICATION")
        return False, "Vote modification blocked - chain integrity compromised", violation
    
    def delete_votes(self, count):
        """Attempt to delete votes (admin function - will break chain)"""
        violation = self.break_chain_on_admin_modification("VOTE_DELETION")
        return False, "Vote deletion blocked - blockchain immutability violated", violation
    
    def reset_chain(self):
        """Reset blockchain chain (admin function - will break chain)"""
        violation = self.break_chain_on_admin_modification("CHAIN_RESET")
        return False, "Chain modification blocked - integrity violation detected", violation
    
    def get_chain_status(self):
        """Get current chain status"""
        return {
            "broken": self.chain_broken,
            "integrity_verified": self.verify_chain_integrity(),
            "total_blocks": len(self.blockchain.chain) if self.blockchain else len(self.mock_votes),
            "status": "COMPROMISED" if self.chain_broken else "SECURE"
        }
    
    def add_vote_to_blockchain(self, vote_data):
        """Add vote to blockchain (for initial demo data only)"""
        try:
            if self.blockchain:
                vote_string = f"{vote_data['candidate']}_{vote_data['voter_id']}_{vote_data['timestamp']}"
                vote_hash = compute_sha256_hex(vote_string)
                block = self.blockchain.add_block(vote_hash)
                append_block(vote_string)
            
            self.mock_votes.append(vote_data)
            return True, "Vote recorded"
        except Exception as e:
            return False, str(e)
