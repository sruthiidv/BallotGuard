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
        self.chain_broken = False
        self.original_chain_state = None
        
        if BLOCKCHAIN_AVAILABLE:
            try:
                self.blockchain = Blockchain()
                self.original_chain_state = self.get_chain_hash()
                print("✅ Blockchain initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize blockchain: {e}")
                print("📝 Using mock blockchain for demo")
                self.blockchain = None
        
        # Initialize with demo blockchain data
        self.init_blockchain_demo_data()
    
    def init_blockchain_demo_data(self):
        """Initialize blockchain with demo voting data"""
        demo_votes = [
            {"election_id": 1, "candidate_id": 1, "voter_hash": "voter_001_hash", "timestamp": time.time() - 3600},
            {"election_id": 1, "candidate_id": 2, "voter_hash": "voter_002_hash", "timestamp": time.time() - 3500},
            {"election_id": 1, "candidate_id": 1, "voter_hash": "voter_003_hash", "timestamp": time.time() - 3400},
            {"election_id": 1, "candidate_id": 3, "voter_hash": "voter_004_hash", "timestamp": time.time() - 3300},
            {"election_id": 1, "candidate_id": 2, "voter_hash": "voter_005_hash", "timestamp": time.time() - 3200},
            {"election_id": 1, "candidate_id": 1, "voter_hash": "voter_006_hash", "timestamp": time.time() - 3100},
            {"election_id": 1, "candidate_id": 2, "voter_hash": "voter_007_hash", "timestamp": time.time() - 3000}
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
                return self.compute_hash(chain_data)
            return "mock_chain_hash"
        except Exception as e:
            return f"error_{str(e)}"
    
    def compute_hash(self, data):
        """Compute SHA256 hash"""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_chain_integrity(self):
        """Verify if blockchain chain is intact"""
        try:
            if self.chain_broken:
                return False
            current_hash = self.get_chain_hash()
            return current_hash == self.original_chain_state
        except:
            return False
    
    def add_vote_to_blockchain(self, vote_data):
        """Add vote to blockchain"""
        try:
            if self.chain_broken:
                return False, "Blockchain chain is broken due to admin modification attempt"
                
            if self.blockchain:
                # Create vote hash from vote data
                vote_string = f"{vote_data['election_id']}_{vote_data['candidate_id']}_{vote_data['voter_hash']}_{vote_data['timestamp']}"
                vote_hash = self.compute_hash(vote_string)
                
                # Add to blockchain
                block = self.blockchain.add_block(vote_hash)
                
                return True, f"Vote recorded in block #{block.index}"
            else:
                # Mock mode
                return True, "Vote recorded (mock mode)"
                
        except Exception as e:
            print(f"❌ Error adding vote to blockchain: {e}")
            return False, str(e)
    
    def get_blockchain_info(self):
        """Get comprehensive blockchain information"""
        try:
            if self.blockchain:
                info = {
                    "total_blocks": len(self.blockchain.chain),
                    "genesis_hash": self.blockchain.chain[0].hash if self.blockchain.chain else "N/A",
                    "latest_hash": self.blockchain.chain[-1].hash if self.blockchain.chain else "N/A",
                    "blockchain_file_exists": os.path.exists("blockchain.json"),
                    "chain_broken": self.chain_broken,
                    "integrity_verified": self.verify_chain_integrity(),
                    "votes_in_chain": len(self.blockchain.chain) - 1,  # Exclude genesis block
                    "chain_size_bytes": self.estimate_chain_size()
                }
            else:
                info = {
                    "total_blocks": 8,  # Mock data
                    "blockchain_file_exists": True,
                    "mode": "mock",
                    "chain_broken": self.chain_broken,
                    "integrity_verified": not self.chain_broken,
                    "votes_in_chain": 7,
                    "chain_size_bytes": 2048
                }
            
            return info
            
        except Exception as e:
            return {
                "error": str(e),
                "chain_broken": True,
                "integrity_verified": False
            }
    
    def estimate_chain_size(self):
        """Estimate blockchain size in bytes"""
        try:
            if self.blockchain:
                return len(self.blockchain.chain) * 256  # Approximate bytes per block
            return 2048  # Mock size
        except:
            return 0
    
    def get_recent_blocks(self, limit=10):
        """Get recent blockchain blocks for display"""
        try:
            if self.blockchain:
                recent_blocks = []
                blocks_to_show = self.blockchain.chain[-limit:] if len(self.blockchain.chain) > limit else self.blockchain.chain
                
                for block in blocks_to_show:
                    recent_blocks.append({
                        "index": block.index,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp)),
                        "hash": block.hash[:16] + "..." if not self.chain_broken else "COMPROMISED",
                        "previous_hash": block.previous_hash[:16] + "..." if block.previous_hash != "0" else "GENESIS",
                        "status": "COMPROMISED" if self.chain_broken else "VALID",
                        "vote_hash": block.vote_hash[:16] + "..." if hasattr(block, 'vote_hash') else "N/A"
                    })
                
                return recent_blocks
            else:
                # Mock recent blocks
                return [
                    {
                        "index": i, 
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), 
                        "hash": f"mock_hash_{i}..." if not self.chain_broken else "COMPROMISED",
                        "previous_hash": f"prev_{i-1}..." if i > 1 else "GENESIS",
                        "status": "COMPROMISED" if self.chain_broken else "VALID",
                        "vote_hash": f"vote_hash_{i}..."
                    }
                    for i in range(max(1, 8 - limit + 1), 9)  # Mock 8 blocks total
                ]
                
        except Exception as e:
            print(f"Error getting recent blocks: {e}")
            return []
    
    def break_chain_on_admin_modification(self, modification_type):
        """Break chain when admin tries to modify blockchain"""
        self.chain_broken = True
        
        violation_details = {
            "timestamp": time.time(),
            "modification_type": modification_type,
            "chain_status": "BROKEN",
            "integrity_violation": True,
            "admin_attempted_modification": True
        }
        
        return violation_details
    
    def get_chain_status(self):
        """Get current chain status"""
        return {
            "broken": self.chain_broken,
            "integrity_verified": self.verify_chain_integrity(),
            "total_blocks": len(self.blockchain.chain) if self.blockchain else 8,
            "status": "COMPROMISED" if self.chain_broken else "SECURE"
        }
    
    def get_vote_verification_info(self, vote_hash=None):
        """Get vote verification information from blockchain"""
        try:
            if self.chain_broken:
                return {
                    "verified": False,
                    "message": "Cannot verify - blockchain chain is broken",
                    "status": "COMPROMISED"
                }
            
            verification_info = {
                "blockchain_intact": self.verify_chain_integrity(),
                "total_verified_votes": len(self.blockchain.chain) - 1 if self.blockchain else 7,
                "verification_method": "SHA-256 cryptographic hashing",
                "last_verification": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "VERIFIED" if self.verify_chain_integrity() else "COMPROMISED"
            }
            
            return verification_info
            
        except Exception as e:
            return {
                "verified": False,
                "message": f"Verification error: {str(e)}",
                "status": "ERROR"
            }

if __name__ == "__main__":
    bc = BlockchainConnector()
    info = bc.get_blockchain_info()
    print(f"Blockchain test: {info.get('total_blocks', 0)} blocks")
