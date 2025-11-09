import requests
import json
import time

class APIClient:
    def __init__(self):
        self.BASE_URL = "http://127.0.0.1:8443"
    
    def api_request(self, method, endpoint, data=None):
        """Helper for API requests with error handling"""
        try:
            url = f"{self.BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=8)
            else:
                response = requests.post(url, json=data, timeout=10)

            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.ConnectionError as e:
            # Connection refused / server not running
            friendly = (
                "Cannot connect to the backend server.\n"
                "Please start the BallotGuard server and try again.\n\n"
                "From the project root open PowerShell and run:\n"
                "    python server\server.py\n\n"
                "Then retry this action. If the server is running on a different host/port, update APIClient.BASE_URL accordingly."
            )
            return False, friendly
        except requests.RequestException as e:
            # Other request-related errors (timeouts, HTTP errors)
            try:
                # If server returned JSON error, surface it
                resp = getattr(e, 'response', None)
                if resp is not None and resp.headers.get('content-type', '').startswith('application/json'):
                    return False, resp.json()
            except Exception:
                pass
            return False, str(e)

    # Election Management
    def get_elections(self):
        return self.api_request("GET", "/elections")

    def get_election(self, election_id):
        return self.api_request("GET", f"/elections/{election_id}")

    def get_election_results(self, election_id):
        """Get detailed election results including vote counts and blockchain status"""
        return self.api_request("GET", f"/elections/{election_id}/results")

    def create_election(self, data):
        return self.api_request("POST", "/elections", data)

    def election_action(self, election_id, action):
        """Execute election action (open/close/pause/resume/tally)"""
        return self.api_request("POST", f"/elections/{election_id}/{action}")

    def export_proof(self, election_id):
        return self.api_request("GET", f"/elections/{election_id}/proof")

    def archive_election(self, election_id):
        return self.api_request("POST", f"/elections/{election_id}/archive")

    def reset_election(self, election_id):
        return self.api_request("POST", f"/elections/{election_id}/reset")
    
    # Voter Management 
    def get_voters(self):
        return self.api_request("GET", "/voters")

    def enroll_voter(self, voter_data):
        return self.api_request("POST", "/voters/enroll", voter_data)

    def approve_voter(self, voter_id):
        return self.api_request("POST", f"/voters/{voter_id}/approve")

    def block_voter(self, voter_id):
        return self.api_request("POST", f"/voters/{voter_id}/block")

    # Blockchain & Verification
    def verify_blockchain(self, election_id):
        """Verify blockchain integrity for an election"""
        return self.api_request("GET", f"/blockchain/verify/{election_id}")

    def verify_ledger(self, election_id):
        return self.api_request("GET", f"/ledger/verify?election_id={election_id}")

    def get_last_block(self, election_id):
        return self.api_request("GET", f"/ledger/last?election_id={election_id}")

    def get_system_health(self):
        return self.api_request("GET", "/health")
