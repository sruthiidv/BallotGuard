import sys
import os
import json
import time
from datetime import datetime
import requests

class DatabaseConnector:
    def __init__(self, flask_server_url="http://localhost:5000"):
        self.flask_server_url = flask_server_url
        self.db_available = self.test_connection()
        
        if not self.db_available:
            print("⚠️ Flask server not available, using mock data")
            self.init_mock_data()
    
    def test_connection(self):
        """Test connection to Flask server"""
        try:
            response = requests.get(f"{self.flask_server_url}/test-db", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Database connection successful: {data['database_status']}")
                print(f"📊 Elections: {data['elections']}, Votes: {data['votes']}, Voters: {data['voters']}")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Flask server: {e}")
            return False
    
    def init_mock_data(self):
        """Initialize mock data if database unavailable"""
        self.mock_elections = [{
            'id': 1,
            'title': 'Student Council Election 2024 (MOCK)',
            'description': 'Mock election data - Flask server not connected',
            'start_date': datetime.now().isoformat(),
            'end_date': datetime.now().isoformat(),
            'status': 'active',
            'candidates': [
                {'id': 1, 'name': 'Alice Johnson', 'party': 'Progressive Party', 'votes': 3, 'percentage': 42.9},
                {'id': 2, 'name': 'Bob Smith', 'party': 'Conservative Party', 'votes': 2, 'percentage': 28.6},
                {'id': 3, 'name': 'Carol Davis', 'party': 'Independent', 'votes': 2, 'percentage': 28.6}
            ],
            'total_votes': 7,
            'eligible_voters': 1000,
            'created_by': 'admin',
            'created_at': datetime.now().isoformat()
        }]
    
    def get_elections(self):
        """Get all elections"""
        if not self.db_available:
            return True, "Mock data loaded", self.mock_elections
        
        try:
            response = requests.get(f"{self.flask_server_url}/api/elections", timeout=10)
            if response.status_code == 200:
                elections = response.json()
                return True, "Elections retrieved from database", elections
            else:
                return False, f"Server error: {response.status_code}", []
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", []
    
    def get_election_by_id(self, election_id):
        """Get specific election by ID"""
        if not self.db_available:
            for election in self.mock_elections:
                if election['id'] == election_id:
                    return True, "Mock election found", election
            return False, "Mock election not found", None
        
        try:
            response = requests.get(f"{self.flask_server_url}/api/elections/{election_id}", timeout=10)
            if response.status_code == 200:
                election = response.json()
                return True, "Election found", election
            elif response.status_code == 404:
                return False, "Election not found", None
            else:
                return False, f"Server error: {response.status_code}", None
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", None
    
    def get_election_results(self, election_id):
        """Get detailed election results"""
        success, message, election = self.get_election_by_id(election_id)
        if not success:
            return False, message, None
        
        try:
            # Calculate detailed results
            results = {
                'election_id': election['id'],
                'title': election['title'],
                'description': election['description'],
                'status': election['status'],
                'total_votes': election.get('total_votes', 0),
                'eligible_voters': election['eligible_voters'],
                'turnout_percentage': (election.get('total_votes', 0) / election['eligible_voters']) * 100,
                'candidates': election.get('candidates', []),
                'vote_distribution': {},
                'timestamps': []
            }
            
            # Sort candidates by votes
            results['candidates'].sort(key=lambda x: x.get('votes', 0), reverse=True)
            
            # Create vote distribution
            for candidate in results['candidates']:
                results['vote_distribution'][candidate['name']] = candidate.get('votes', 0)
            
            return True, "Results retrieved successfully", results
            
        except Exception as e:
            return False, f"Error processing results: {str(e)}", None
    
    def create_election(self, election_data):
        """Create a new election"""
        if not self.db_available:
            return False, "Cannot create election: Database not connected", None
        
        try:
            response = requests.post(
                f"{self.flask_server_url}/api/elections",
                json=election_data,
                timeout=10
            )
            
            if response.status_code == 201:
                election = response.json()
                return True, "Election created successfully", election.get('id')
            else:
                try:
                    error_data = response.json()
                    return False, error_data.get('error', f"Server error: {response.status_code}"), None
                except:
                    return False, f"Server error: {response.status_code}", None
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", None
    
    def update_election_status(self, election_id, status):
        """Update election status"""
        if not self.db_available:
            return False, "Cannot update election: Database not connected", None
        
        try:
            response = requests.patch(
                f"{self.flask_server_url}/api/elections/{election_id}",
                json={"status": status},
                timeout=10
            )
            
            if response.status_code == 200:
                election = response.json()
                return True, f"Election status updated to {status}", election
            else:
                return False, f"Server error: {response.status_code}", None
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", None
    
    def get_voters(self, election_id=None):
        """Get voters"""
        if not self.db_available:
            return True, "Mock voters data", []
        
        try:
            url = f"{self.flask_server_url}/api/voters"
            if election_id:
                url += f"?election_id={election_id}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                voters = response.json()
                return True, "Voters retrieved successfully", voters
            else:
                return False, f"Server error: {response.status_code}", []
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", []
    
    def get_votes(self, election_id=None):
        """Get votes"""
        if not self.db_available:
            return True, "Mock votes data", []
        
        try:
            url = f"{self.flask_server_url}/api/votes"
            if election_id:
                url += f"?election_id={election_id}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                votes = response.json()
                return True, "Votes retrieved successfully", votes
            else:
                return False, f"Server error: {response.status_code}", []
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", []
    
    def get_database_stats(self):
        """Get database statistics"""
        if not self.db_available:
            return True, "Mock database stats", {
                'total_elections': 1,
                'active_elections': 1,
                'total_voters': 10,
                'total_votes': 7,
                'database_status': 'Mock Mode',
                'last_updated': datetime.now().isoformat()
            }
        
        try:
            response = requests.get(f"{self.flask_server_url}/test-db", timeout=10)
            if response.status_code == 200:
                data = response.json()
                stats = {
                    'total_elections': data.get('elections', 0),
                    'active_elections': data.get('elections', 0),
                    'total_voters': data.get('voters', 0),
                    'total_votes': data.get('votes', 0),
                    'database_status': data.get('database_status', 'Unknown'),
                    'last_updated': datetime.now().isoformat()
                }
                return True, "Database stats retrieved", stats
            else:
                return False, f"Server error: {response.status_code}", {}
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}", {}

# Test function
def test_database_connection():
    """Test database connectivity"""
    print("🧪 Testing Database Connection...")
    
    db_connector = DatabaseConnector()
    
    if db_connector.db_available:
        print("✅ Database connection test PASSED")
        
        # Test getting elections
        success, message, elections = db_connector.get_elections()
        print(f"📊 Elections test: {message}")
        print(f"📈 Found {len(elections) if elections else 0} elections")
        
        return True
    else:
        print("❌ Database connection test FAILED")
        print("🔧 Make sure Flask server is running on http://localhost:5000")
        return False

if __name__ == "__main__":
    test_database_connection()
