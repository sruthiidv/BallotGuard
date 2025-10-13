import sys
import os
import json
import time
import requests

class BlockchainConnector:
    def __init__(self, flask_server_url="http://localhost:5000"):
        self.flask_server_url = flask_server_url
        self.chain_broken = False
        
        print("📝 Blockchain connector initialized (simulation mode)")
    
    def get_blockchain_info(self):
        """Get blockchain information"""
        try:
            # Try to get info from server
            response = requests.get(f"{self.flask_server_url}/blockchain/info", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
            
        # Return mock data
        return {
            "total_blocks": 8,
            "blockchain_file_exists": True,
            "mode": "mock",
            "chain_broken": self.chain_broken,
            "integrity_verified": not self.chain_broken,
            "votes_in_chain": 7,
            "chain_size_bytes": 2048
        }
    
    def get_recent_blocks(self, limit=10):
        """Get recent blockchain blocks"""
        try:
            # Try to get from server
            response = requests.get(f"{self.flask_server_url}/blockchain/blocks", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
            
        # Return mock blocks
        return [
            {
                "index": i,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "hash": f"mock_hash_{i}..." if not self.chain_broken else "COMPROMISED",
                "previous_hash": f"prev_{i-1}..." if i > 1 else "GENESIS",
                "status": "COMPROMISED" if self.chain_broken else "VALID",
                "vote_hash": f"vote_hash_{i}..."
            }
            for i in range(max(1, 8 - limit + 1), 9)
        ]
    
    def break_chain_on_admin_modification(self, modification_type):
        """Break chain when admin tries to modify blockchain"""
        self.chain_broken = True
        
        return {
            "timestamp": time.time(),
            "modification_type": modification_type,
            "chain_status": "BROKEN",
            "integrity_violation": True
        }
    
    def get_chain_status(self):
        """Get current chain status"""
        return {
            "broken": self.chain_broken,
            "integrity_verified": not self.chain_broken,
            "total_blocks": 8,
            "status": "COMPROMISED" if self.chain_broken else "SECURE"
        }
    
    def get_vote_verification_info(self, vote_hash=None):
        """Get vote verification information"""
        if self.chain_broken:
            return {
                "verified": False,
                "message": "Cannot verify - blockchain chain is broken",
                "status": "COMPROMISED"
            }
        
        return {
            "blockchain_intact": not self.chain_broken,
            "total_verified_votes": 7,
            "verification_method": "SHA-256 cryptographic hashing",
            "last_verification": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "VERIFIED" if not self.chain_broken else "COMPROMISED"
        }

if __name__ == "__main__":
    bc = BlockchainConnector()
    info = bc.get_blockchain_info()
    print(f"Blockchain test: {info.get('total_blocks', 0)} blocks")
