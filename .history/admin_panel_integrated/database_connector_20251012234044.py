# ... (Existing imports and class structure)

class DatabaseConnector:
    def __init__(self, flask_server_url="http://localhost:5000"):
        self.flask_server_url = flask_server_url
        self.db_available = self.test_connection()
        
        if not self.db_available:
            print("⚠️ Flask server not available, using mock data")
            self.init_mock_data()
            
    # ... (Existing methods: test_connection, init_mock_data, get_elections, get_election_by_id, get_election_results, create_election, update_election_status, get_voters, get_votes, get_database_stats)

    def delete_election(self, election_id):
        """Delete an election by ID"""
        if not self.db_available:
            # Handle mock data deletion if necessary, for now just fail/success mock
            if any(e['id'] == election_id for e in self.mock_elections):
                self.mock_elections = [e for e in self.mock_elections if e['id'] != election_id]
                return True, f"Mock election ID {election_id} deleted successfully"
            return False, "Cannot delete: Database not connected or Mock ID not found"

        try:
            response = requests.delete(
                f"{self.flask_server_url}/api/elections/{election_id}",
                timeout=10
            )
            
            if response.status_code == 204: # No Content status for successful deletion
                return True, f"Election ID {election_id} deleted successfully"
            elif response.status_code == 404:
                return False, f"Election ID {election_id} not found"
            else:
                return False, f"Server error on deletion: {response.status_code}", None
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", None

# ... (Existing test function)