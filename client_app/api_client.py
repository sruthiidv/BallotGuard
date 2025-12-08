import requests
import json
import base64
import urllib3
# Import cryptographic libraries (REQUIRED - no fallback)
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

# Disable SSL warnings for self-signed certificates (development only)
# For production, use proper CA-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from client_app.client_config import SERVER_BASE
except ImportError:
    from client_config import SERVER_BASE

class BallotGuardAPI:
    def __init__(self, server_base=None):
        self.server_base = server_base or SERVER_BASE
        self.rsa_pub_pem = None  # Cache server's public key
        # For self-signed certificates, disable SSL verification in development
        # For production, use verify='/path/to/ca-bundle.crt'
        self.verify_ssl = False if self.server_base.startswith('https://') else True
        self._fetch_server_public_key()
    
    def _fetch_server_public_key(self):
        """Fetch and cache server's RSA public key for signature verification
        Auto-fallback to HTTP if HTTPS connection fails"""
        try:
            response = requests.get(f"{self.server_base}/public-key", timeout=5, verify=self.verify_ssl)
            if response.status_code == 200:
                self.rsa_pub_pem = response.json().get("rsa_pub_pem")
                if not self.rsa_pub_pem:
                    print("WARNING: Server did not provide RSA public key")
            else:
                print(f"WARNING: Could not fetch server public key: {response.status_code}")
        except requests.exceptions.SSLError as e:
            # HTTPS failed, try HTTP fallback
            if self.server_base.startswith('https://'):
                print(f"[CLIENT] ⚠ HTTPS connection failed (no certificates), falling back to HTTP")
                self.server_base = self.server_base.replace('https://', 'http://')
                self.verify_ssl = True  # HTTP doesn't need SSL verification
                try:
                    response = requests.get(f"{self.server_base}/public-key", timeout=5)
                    if response.status_code == 200:
                        self.rsa_pub_pem = response.json().get("rsa_pub_pem")
                        print(f"[CLIENT] ✓ Connected to server via HTTP: {self.server_base}")
                except Exception as fallback_error:
                    print(f"[CLIENT] ✗ HTTP fallback also failed: {fallback_error}")
            else:
                print(f"WARNING: Failed to fetch server public key: {e}")
        except Exception as e:
            print(f"WARNING: Failed to fetch server public key: {e}")
    
    def verify_signature(self, data, signature_b64):
        """Verify RSA-PSS signature on JSON data"""
        if not self.rsa_pub_pem:
            print("[CLIENT] ✗ ERROR: No server public key available, cannot verify signature")
            return False
        
        try:
            # Serialize data to canonical JSON
            data_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
            h = SHA256.new(data_bytes)
            
            # Import public key and verify
            pub_key = RSA.import_key(self.rsa_pub_pem)
            verifier = pss.new(pub_key)
            verifier.verify(h, base64.b64decode(signature_b64))
            print(f"[CLIENT] ✓ Signature verification PASSED ({len(data_bytes)} bytes verified)")
            return True
        except Exception as e:
            print(f"[CLIENT] ✗ Signature verification FAILED: {e}")
            return False
    
    def get_elections(self):
        """Get list of all elections"""
        try:
            response = requests.get(f"{self.server_base}/elections", timeout=5, verify=self.verify_ssl)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Server error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def enroll_voter(self, face_encoding, name=None):
        """Enroll a new voter - MVP Architecture endpoint (now expects face_encoding and optional name)"""
        try:
            data = {
                "face_encoding": face_encoding,
                "name": name or "Anonymous"
            }
            response = requests.post(f"{self.server_base}/voters/enroll", json=data, timeout=10, verify=self.verify_ssl)
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
            response = requests.post(f"{self.server_base}/auth/face/verify", json=data, timeout=10, verify=self.verify_ssl)
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", "Verification failed")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def issue_ovt(self, voter_id, election_id):
        """Issue OVT token - MVP Architecture endpoint with signature verification"""
        try:
            data = {
                "voter_id": voter_id,
                "election_id": election_id
            }
            response = requests.post(f"{self.server_base}/ovt/issue", json=data, timeout=10, verify=self.verify_ssl)
            
            if response.status_code == 200:
                ovt_response = response.json()
                
                # CRITICAL SECURITY: Verify server's signature on OVT
                if "server_sig" in ovt_response and "ovt" in ovt_response:
                    ovt_data = ovt_response["ovt"]
                    server_sig = ovt_response["server_sig"]
                    
                    print(f"[CLIENT] Verifying OVT signature for ovt_uuid={ovt_data.get('ovt_uuid')}...")
                    if not self.verify_signature(ovt_data, server_sig):
                        print(f"[CLIENT] ✗ SECURITY ALERT: OVT signature verification FAILED!")
                        return None, "OVT signature verification failed! Possible tampering detected."
                    
                    print(f"[CLIENT] ✓ OVT signature verified successfully - token is authentic")
                else:
                    print("[CLIENT] ⚠ WARNING: OVT response missing signature field")
                
                return ovt_response, None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", "Failed to issue voting token")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def cast_vote(self, vote_data):
        """Cast a vote - MVP Architecture endpoint"""
        try:
            response = requests.post(f"{self.server_base}/votes", json=vote_data, timeout=10, verify=self.verify_ssl)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", f"Server error: {response.status_code}")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"

    def get_voters(self, status=None):
        """Return list of voters. Optional status filter: 'pending' or 'active'."""
        try:
            url = f"{self.server_base}/voters"
            if status:
                url = f"{url}?status={status}"
            response = requests.get(url, timeout=8, verify=self.verify_ssl)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Server error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"

    def get_voter_status(self, voter_id):
        """Get voter's global status - DEPRECATED: Use get_voter_election_status for per-election check"""
        try:
            # This returns global voter status, not election-specific
            response = requests.get(f"{self.server_base}/voters?status=all", timeout=5, verify=self.verify_ssl)
            if response.status_code == 200:
                voters = response.json()
                for v in voters:
                    if v.get('voter_id') == voter_id:
                        return v.get('status'), None
                return None, "Voter not found"
            return None, f"Server error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
    
    def get_voter_election_status(self, voter_id, election_id):
        """Check if voter is approved for a specific election"""
        try:
            response = requests.get(
                f"{self.server_base}/voters/{voter_id}/election-status/{election_id}",
                timeout=5,
                verify=self.verify_ssl
            )
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
            response = requests.post(f"{self.server_base}/elections/{election_id}/{action}", timeout=10, verify=self.verify_ssl)
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
            response = requests.get(f"{self.server_base}/elections/{election_id}/results", timeout=10, verify=self.verify_ssl)
            if response.status_code == 200:
                return response.json(), None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", {}).get("message", f"Server error: {response.status_code}")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"