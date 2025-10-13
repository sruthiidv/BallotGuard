def get_blockchain_info(self):
    """Get blockchain info from server"""
    if not self.db_available:
        return self.get_mock_blockchain_info()
    
    try:
        response = requests.get(f"{self.flask_server_url}/blockchain/info", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Blockchain service unavailable"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_recent_blocks(self, limit=10):
    """Get recent blockchain blocks"""
    if not self.db_available:
        return self.get_mock_blocks(limit)
    
    try:
        response = requests.get(f"{self.flask_server_url}/blockchain/blocks", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.RequestException as e:
        return []

def verify_blockchain_integrity(self):
    """Verify blockchain through server"""
    if not self.db_available:
        return {"status": "Mock mode"}
    
    try:
        response = requests.get(f"{self.flask_server_url}/blockchain/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "verified": data.get("chain_valid", False),
                "message": data.get("validation_message", "Unknown"),
                "status": "VERIFIED" if data.get("chain_valid") else "COMPROMISED"
            }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
