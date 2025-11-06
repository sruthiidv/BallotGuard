import requests
import json
try:
    from client_app.client_config import SERVER_BASE
except ImportError:
    from client_config import SERVER_BASE

class BallotGuardAPI:
    def __init__(self, server_base=None):
        self.server_base = server_base or SERVER_BASE
    
    def get_elections(self):
        """Get list of all elections"""
        try:
            response = requests.get(f"{self.server_base}/elections", timeout=5)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Server error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def enroll_voter(self, face_encoding):
        """Enroll a new voter - MVP Architecture endpoint (now expects face_encoding)"""
        try:
            data = {"face_encoding": face_encoding}
            response = requests.post(f"{self.server_base}/voters/enroll", json=data, timeout=10)
            if response.status_code == 201:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", f"Server error: {response.status_code}")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def verify_face(self, voter_id, election_id, face_encoding):
        """Face verification - MVP Architecture endpoint (now expects face_encoding)"""
        try:
            data = {
                "voter_id": voter_id,
                "election_id": election_id,
                "face_encoding": face_encoding
            }
            response = requests.post(f"{self.server_base}/auth/face/verify", json=data, timeout=10)
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", "Verification failed")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def issue_ovt(self, voter_id, election_id):
        """Issue OVT token - MVP Architecture endpoint"""
        try:
            data = {
                "voter_id": voter_id,
                "election_id": election_id
            }
            response = requests.post(f"{self.server_base}/ovt/issue", json=data, timeout=10)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", "Failed to issue voting token")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def cast_vote(self, vote_data):
        """Cast a vote - MVP Architecture endpoint"""
        try:
            response = requests.post(f"{self.server_base}/votes", json=vote_data, timeout=10)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", f"Server error: {response.status_code}")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def update_election_status(self, election_id, action):
        """Update election status (open/close/pause/resume/tally)"""
        try:
            response = requests.post(f"{self.server_base}/elections/{election_id}/{action}", timeout=10)
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", f"Server error: {response.status_code}")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def get_election_results(self, election_id):
        """Get election results - MVP Architecture endpoint"""
        try:
            response = requests.get(f"{self.server_base}/elections/{election_id}/proof", timeout=10)
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", f"Server error: {response.status_code}")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"