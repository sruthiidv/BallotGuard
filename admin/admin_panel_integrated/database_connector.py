import sys
import os
import json
import time
from datetime import datetime, timedelta
import requests

class DatabaseConnector:
    def __init__(self, flask_server_url="http://127.0.0.1:8443"):
        self.flask_server_url = flask_server_url
        print(f"📡 Database connector initialized")
        print(f"🔗 Connecting to server: {flask_server_url}")
        self.test_connection()
    
    def test_connection(self):
        """Test connection to Flask server - raises exception if unavailable"""
        try:
            response = requests.get(f"{self.flask_server_url}/test-db", timeout=5)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Database connection successful: {data.get('database_status', 'Connected')}")
            print(f"📊 Elections: {data.get('elections', 0)}, Votes: {data.get('votes', 0)}, Voters: {data.get('voters', 0)}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Flask server at {self.flask_server_url}: {e}")

    
    def get_elections(self):
        """Retrieve all elections from server"""
        try:
            response = requests.get(f"{self.flask_server_url}/api/elections", timeout=8)
            response.raise_for_status()
            return True, "Elections retrieved successfully", response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to get elections from server: {e}") 

    def get_election_by_id(self, election_id):
        """Retrieve a specific election by ID from server"""
        try:
            response = requests.get(f"{self.flask_server_url}/api/elections/{election_id}", timeout=8)
            response.raise_for_status()
            return True, "Election retrieved successfully", response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to get election {election_id} from server: {e}")

    def create_election(self, election_data):
        """Create a new election on server"""
        try:
            response = requests.post(
                f"{self.flask_server_url}/api/elections",
                json=election_data,
                timeout=8
            )
            response.raise_for_status()
            data = response.json()
            election_id = data.get('id')
            return True, f"Election created successfully (ID: {election_id})", election_id
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to create election on server: {e}")

    def delete_election(self, election_id):
        """Delete an election by ID on server"""
        try:
            response = requests.delete(
                f"{self.flask_server_url}/api/elections/{election_id}",
                timeout=8
            )
            response.raise_for_status()
            return True, f"Election ID {election_id} deleted successfully"
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to delete election {election_id} from server: {e}")
        
    def get_election_results(self, election_id):
        """Retrieve tallied results for an election from server"""
        try:
            url = f"{self.flask_server_url}/api/elections/{election_id}/results"
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to get election results from server: {e}")
        
    # Other methods (update_election_status, etc.) could be implemented similarly

# ... (rest of the file is assumed to contain other methods or main block)