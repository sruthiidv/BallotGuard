import sys
import os
import json
import time
from datetime import datetime, timedelta
import requests

class DatabaseConnector:
    def __init__(self, flask_server_url="http://127.0.0.1:8443"):
        self.flask_server_url = flask_server_url
        
        # This call must be correctly indented to work
        self.db_available = self.test_connection()
        
        if not self.db_available:
            print("⚠️ Flask server not available, using mock data")
            self.init_mock_data()
    
    # --- Ensure this method is correctly indented inside the class ---
    def test_connection(self):
        """Test connection to Flask server"""
        try:
            # We are using a mock endpoint here since the original server is likely not running
            response = requests.get(f"{self.flask_server_url}/test-db", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Database connection successful: {data.get('database_status', 'Connected')}")
                print(f"📊 Elections: {data.get('elections', 0)}, Votes: {data.get('votes', 0)}, Voters: {data.get('voters', 0)}")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            # When the connection fails, it falls back to mock data
            print(f"❌ Cannot connect to Flask server: {e}")
            return False
            
    def init_mock_data(self):
        """Initialize mock data if database unavailable"""
        self.mock_elections = [{
            'id': 1,
            'title': 'Student Council Election 2024 (MOCK)',
            'description': 'Mock election data - Flask server not connected',
            'start_date': (datetime.now() - timedelta(days=1)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=5)).isoformat(),
            'status': 'ACTIVE',
            'eligible_voters': 1200,
            'votes_cast': 750,
            'candidates': [{'name': 'Anya Smith', 'party': 'Blue'}, {'name': 'Ben Jones', 'party': 'Red'}]
        },
        {
            'id': 2,
            'title': 'Board of Directors Vote (MOCK)',
            'description': 'Vote for the new members of the Board.',
            'start_date': (datetime.now() - timedelta(days=30)).isoformat(),
            'end_date': (datetime.now() - timedelta(days=15)).isoformat(),
            'status': 'CLOSED',
            'eligible_voters': 200,
            'votes_cast': 180,
            'candidates': [{'name': 'Cathy King', 'party': 'Green'}, {'name': 'David Lee', 'party': 'Yellow'}]
        }]
        print("✅ Mock data initialized.")
    
    def get_elections(self):
        """Retrieve all elections"""
        if not self.db_available:
            return True, "Mock data retrieved", self.mock_elections

        # Actual API call logic here... (omitted for brevity, use your Flask logic)
        return False, "Database not connected for retrieval", [] 

    def get_election_by_id(self, election_id):
        """Retrieve a specific election by ID"""
        if not self.db_available:
            election = next((e for e in self.mock_elections if e['id'] == election_id), None)
            if election:
                return True, "Mock election retrieved", election
            return False, f"Mock election ID {election_id} not found", None

        # Actual API call logic here...
        return False, "Database not connected for retrieval", None

    def create_election(self, election_data):
        """Create a new election and return its ID (Mocked for now)"""
        if not self.db_available:
            new_id = max([e['id'] for e in self.mock_elections]) + 1 if self.mock_elections else 1
            new_election = {
                'id': new_id,
                'status': 'PENDING',
                'votes_cast': 0,
                **election_data
            }
            self.mock_elections.append(new_election)
            return True, "Mock election created successfully", new_id

        # Actual API call logic here...
        return False, "Cannot create: Database not connected", None

    # --- NEW: Delete Election Method ---
    def delete_election(self, election_id):
        """Delete an election by ID"""
        if not self.db_available:
            initial_count = len(self.mock_elections)
            self.mock_elections = [e for e in self.mock_elections if e['id'] != election_id]
            if len(self.mock_elections) < initial_count:
                return True, f"Mock election ID {election_id} deleted successfully"
            return False, f"Cannot delete: Mock ID {election_id} not found"

        # Actual API call logic here...
        return False, "Cannot delete: Database not connected", None
        
    def get_election_results(self, election_id):
        """Retrieve tallied results for an election. Returns (True, results) or (False, error)"""
        # Mock path
        if not self.db_available:
            election = next((e for e in self.mock_elections if e['id'] == election_id), None)
            if not election:
                return False, f"Mock election ID {election_id} not found"

            candidates = election.get('candidates', [])
            total_votes = election.get('votes_cast', 0)
            # distribute mock votes evenly
            per = total_votes // len(candidates) if candidates and total_votes else 100
            results = []
            for i, c in enumerate(candidates):
                results.append({
                    'candidate_id': i+1,
                    'name': c.get('name', f'Candidate {i+1}'),
                    'votes': per,
                    'percentage': (per / max(1, total_votes) * 100) if total_votes else 0.0
                })

            # find winner (highest votes)
            if results:
                max_votes = max(r['votes'] for r in results)
                winners = [r for r in results if r['votes'] == max_votes]
                if len(winners) > 1:
                    winner = {'tie': True, 'winners': winners}
                else:
                    winner = winners[0]
            else:
                winner = None

            payload = {
                'election_id': election_id,
                'total_votes': total_votes,
                'eligible_voters': election.get('eligible_voters', 0),
                'turnout_percentage': (total_votes / max(1, election.get('eligible_voters', 1)) * 100) if election.get('eligible_voters') else 0.0,
                'results': results,
                'winner': winner
            }
            return True, payload

        # Live server path
        try:
            url = f"{self.flask_server_url}/api/elections/{election_id}/results"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                return True, resp.json()
            else:
                try:
                    data = resp.json()
                    return False, data.get('error', f"Server returned {resp.status_code}")
                except Exception:
                    return False, f"Server returned status {resp.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}"
        
    # Other methods (update_election_status, etc.) could be implemented similarly

# ... (rest of the file is assumed to contain other methods or main block)