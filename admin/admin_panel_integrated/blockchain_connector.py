import sys
import os
import json
import time
import requests

class BlockchainConnector:
    def __init__(self, flask_server_url="http://localhost:5000"):
        self.flask_server_url = flask_server_url
        self.chain_broken = False
        
        print("📝 Blockchain connector initialized")
        print(f"🔗 Connecting to server: {flask_server_url}")
    
    def get_blockchain_info(self):
        """Get blockchain information from server"""
        try:
            response = requests.get(f"{self.flask_server_url}/blockchain/info", timeout=5)
            response.raise_for_status()
            data = response.json()
            # Merge local chain_broken state with server data
            data['chain_broken'] = self.chain_broken
            data['integrity_verified'] = not self.chain_broken
            return data
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get blockchain info from server: {e}")
    
    def get_recent_blocks(self, limit=10):
        """Get recent blockchain blocks from server"""
        try:
            response = requests.get(
                f"{self.flask_server_url}/blockchain/blocks?limit={limit}",
                timeout=5
            )
            response.raise_for_status()
            blocks = response.json()
            # Update status based on local chain_broken flag
            if self.chain_broken:
                for block in blocks:
                    block['status'] = 'COMPROMISED'
                    block['hash'] = 'COMPROMISED'
            return blocks
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get blockchain blocks from server: {e}")
    
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
        """Get current chain status from server"""
        try:
            response = requests.get(f"{self.flask_server_url}/blockchain/status", timeout=5)
            response.raise_for_status()
            data = response.json()
            # Merge local chain_broken state with server data
            data['broken'] = self.chain_broken
            data['integrity_verified'] = not self.chain_broken
            data['status'] = "COMPROMISED" if self.chain_broken else data.get('status', 'SECURE')
            return data
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get chain status from server: {e}")
    
    def get_vote_verification_info(self, vote_hash=None):
        """Get vote verification information from server"""
        if self.chain_broken:
            return {
                "verified": False,
                "message": "Cannot verify - blockchain chain is broken",
                "status": "COMPROMISED"
            }
        
        try:
            endpoint = f"{self.flask_server_url}/blockchain/verify"
            if vote_hash:
                endpoint += f"?vote_hash={vote_hash}"
            
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            data = response.json()
            # Add local chain state
            data['blockchain_intact'] = not self.chain_broken
            return data
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get verification info from server: {e}")

if __name__ == "__main__":
    bc = BlockchainConnector()
    info = bc.get_blockchain_info()
    print(f"Blockchain test: {info.get('total_blocks', 0)} blocks")
