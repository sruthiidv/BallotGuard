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
        
        if BLOCKCHAIN_AVAILABLE:
            try:
                self.blockchain = Blockchain()
                print("✅ Blockchain initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize blockchain: {e}")
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
        ]
        
        for vote in demo_votes:
            self.add_vote_to_blockchain(vote)
    
    def add_vote_to_blockchain(self, vote_data):
        """Add vote to blockchain (simulates client app voting)"""
        try:
            if self.blockchain:
                # Create vote hash
                vote_string = f"{vote_data['candidate']}_{vote_data['voter_id']}_{vote_data['timestamp']}"
                vote_hash = compute_sha256_hex(vote_string)
                
                # Add to blockchain
                block = self.blockchain.add_block(vote_hash)
                
                # Also add to ledger using your ledger.py
                append_block(vote_string)
                
                print(f"✅ Vote added to blockchain: Block #{block.index}")
                return True, f"Vote recorded in block #{block.index}"
            else:
                # Mock mode - just add to list
                self.mock_votes.append(vote_data)
                return True, "Vote recorded (mock mode)"
                
        except Exception as e:
            print(f"❌ Error adding vote to blockchain: {e}")
            return False, str(e)
    
    def get_vote_tally(self):
        """Get current vote tally from blockchain"""
        try:
            tally = {"Candidate A": 0, "Candidate B": 0, "Candidate C": 0}
            total_votes = 0
            
            if self.blockchain:
                # Real blockchain mode
                for block in self.blockchain.chain[1:]:  # Skip genesis block
                    total_votes += 1
                
                # Get actual tally from mock votes (since we don't decrypt in demo)
                for vote in self.mock_votes:
                    if vote["candidate"] in tally:
                        tally[vote["candidate"]] += 1
            else:
                # Mock mode
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
                "blockchain_blocks": len(self.blockchain.chain) if self.blockchain else 0
            }
            
        except Exception as e:
            print(f"❌ Error getting vote tally: {e}")
            return {
                "candidates": [
                    {"id": "A", "name": "Candidate A", "votes": 0},
                    {"id": "B", "name": "Candidate B", "votes": 0},
                    {"id": "C", "name": "Candidate C", "votes": 0}
                ],
                "total_votes": 0,
                "blockchain_blocks": 0
            }
    
    def get_blockchain_info(self):
        """Get blockchain statistics"""
        try:
            if self.blockchain:
                return {
                    "total_blocks": len(self.blockchain.chain),
                    "genesis_hash": self.blockchain.chain[0].hash if self.blockchain.chain else "N/A",
                    "latest_hash": self.blockchain.chain[-1].hash if self.blockchain.chain else "N/A",
                    "blockchain_file_exists": os.path.exists("blockchain.json")
                }
            else:
                # Try to load from ledger file
                try:
                    chain = load_chain()
                    return {
                        "total_blocks": len(chain),
                        "blockchain_file_exists": len(chain) > 0,
                        "mode": "ledger_file",
                        "latest_hash": chain[-1].get("hash", "N/A") if chain else "N/A"
                    }
                except:
                    return {
                        "total_blocks": 0,
                        "blockchain_file_exists": False,
                        "mode": "mock",
                        "error": "No blockchain data available"
                    }
        except Exception as e:
            return {"error": str(e)}
    
    def simulate_client_vote(self, candidate_name):
        """Simulate a vote coming from client app (for demo purposes)"""
        import random
        
        vote_data = {
            "candidate": candidate_name,
            "voter_id": f"sim_voter_{random.randint(1000, 9999)}",
            "timestamp": time.time()
        }
        
        return self.add_vote_to_blockchain(vote_data)
    
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
                        "hash": block.hash[:16] + "...",  # Shortened hash
                        "previous_hash": block.previous_hash[:16] + "..." if block.previous_hash != "0" else "GENESIS"
                    })
                
                return recent_blocks
            else:
                # Mock recent blocks
                return [
                    {"index": i, "timestamp": time.strftime("%H:%M:%S"), "hash": f"mock_hash_{i}...", "previous_hash": f"prev_{i-1}..."}
                    for i in range(max(1, len(self.mock_votes) - limit + 1), len(self.mock_votes) + 1)
                ]
                
        except Exception as e:
            print(f"Error getting recent blocks: {e}")
            return []
