import sys
import os
import json
import time
from datetime import datetime

# Add server_backend to path to import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server_backend'))

try:
    from database.models import db, Voter, Vote, BlockchainRecord
    DATABASE_AVAILABLE = True
    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"⚠️ Database modules not available: {e}")
    print("📝 Running in simulation mode")
    DATABASE_AVAILABLE = False

class DatabaseConnector:
    def __init__(self):
        self.db_available = DATABASE_AVAILABLE
        self.mock_elections = []
        self.mock_voters = []
        self.mock_votes = []
        
        # Initialize with demo data
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize with demo election data"""
        # Demo election
        demo_election = {
            'id': 1,
            'title': 'Student Council Election 2024',
            'description': 'Annual student council election',
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now()).isoformat(),
            'status': 'active',
            'candidates': [
                {'id': 1, 'name': 'Alice Johnson', 'party': 'Progressive Party', 'votes': 3},
                {'id': 2, 'name': 'Bob Smith', 'party': 'Conservative Party', 'votes': 2},
                {'id': 3, 'name': 'Carol Davis', 'party': 'Independent', 'votes': 2}
            ],
            'total_votes': 7,
            'eligible_voters': 1000,
            'created_by': 'admin',
            'created_at': datetime.now().isoformat()
        }
        
        self.mock_elections.append(demo_election)
        
        # Demo voters
        for i in range(1, 11):
            self.mock_voters.append({
                'id': i,
                'voter_id': f"voter_{i:03d}",
                'name': f"Voter {i}",
                'email': f"voter{i}@example.com",
                'has_voted': i <= 7,  # First 7 have voted
                'vote_timestamp': datetime.now().isoformat() if i <= 7 else None
            })
        
        # Demo votes
        vote_distribution = [1, 2, 1, 3, 2, 1, 2]  # Candidate IDs
        for i, candidate_id in enumerate(vote_distribution):
            self.mock_votes.append({
                'id': i + 1,
                'voter_id': f"voter_{i+1:03d}",
                'candidate_id': candidate_id,
                'election_id': 1,
                'timestamp': datetime.now().isoformat(),
                'blockchain_hash': f"hash_{i+1}"
            })
    
    def create_election(self, election_data):
        """Create a new election"""
        try:
            if self.db_available:
                # In real implementation, create database records
                pass
            
            # Mock implementation
            new_election = {
                'id': len(self.mock_elections) + 1,
                'title': election_data['title'],
                'description': election_data['description'],
                'start_date': election_data['start_date'],
                'end_date': election_data['end_date'],
                'status': 'active',
                'candidates': election_data['candidates'],
                'total_votes': 0,
                'eligible_voters': election_data.get('eligible_voters', 1000),
                'created_by': 'admin',
                'created_at': datetime.now().isoformat()
            }
            
            self.mock_elections.append(new_election)
            
            return True, f"Election '{election_data['title']}' created successfully", new_election['id']
            
        except Exception as e:
            return False, f"Failed to create election: {str(e)}", None
    
    def get_elections(self):
        """Get all elections"""
        try:
            return True, "Elections retrieved successfully", self.mock_elections
        except Exception as e:
            return False, f"Failed to retrieve elections: {str(e)}", []
    
    def get_election_by_id(self, election_id):
        """Get specific election by ID"""
        try:
            for election in self.mock_elections:
                if election['id'] == election_id:
                    return True, "Election found", election
            
            return False, "Election not found", None
            
        except Exception as e:
            return False, f"Error retrieving election: {str(e)}", None
    
    def get_election_results(self, election_id):
        """Get detailed election results"""
        try:
            success, message, election = self.get_election_by_id(election_id)
            if not success:
                return False, message, None
            
            # Calculate detailed results
            results = {
                'election_id': election['id'],
                'title': election['title'],
                'description': election['description'],
                'status': election['status'],
                'total_votes': election['total_votes'],
                'eligible_voters': election['eligible_voters'],
                'turnout_percentage': (election['total_votes'] / election['eligible_voters']) * 100,
                'candidates': [],
                'vote_distribution': {},
                'timestamps': []
            }
            
            # Process candidates
            for candidate in election['candidates']:
                candidate_result = {
                    'id': candidate['id'],
                    'name': candidate['name'],
                    'party': candidate.get('party', 'Independent'),
                    'votes': candidate['votes'],
                    'percentage': (candidate['votes'] / max(election['total_votes'], 1)) * 100
                }
                results['candidates'].append(candidate_result)
                results['vote_distribution'][candidate['name']] = candidate['votes']
            
            # Sort candidates by votes
            results['candidates'].sort(key=lambda x: x['votes'], reverse=True)
            
            # Get vote timestamps for this election
            election_votes = [v for v in self.mock_votes if v['election_id'] == election_id]
            results['timestamps'] = [v['timestamp'] for v in election_votes]
            
            return True, "Results retrieved successfully", results
            
        except Exception as e:
            return False, f"Error retrieving results: {str(e)}", None
    
    def get_voters(self, election_id=None):
        """Get voters for specific election or all voters"""
        try:
            if election_id:
                filtered_voters = [v for v in self.mock_voters if v.get('election_id', 1) == election_id]
                return True, "Voters retrieved successfully", filtered_voters
            else:
                return True, "All voters retrieved successfully", self.mock_voters
        except Exception as e:
            return False, f"Error retrieving voters: {str(e)}", []
    
    def get_votes(self, election_id=None):
        """Get votes for specific election or all votes"""
        try:
            if election_id:
                filtered_votes = [v for v in self.mock_votes if v['election_id'] == election_id]
                return True, "Votes retrieved successfully", filtered_votes
            else:
                return True, "All votes retrieved successfully", self.mock_votes
        except Exception as e:
            return False, f"Error retrieving votes: {str(e)}", []
    
    def update_election_status(self, election_id, status):
        """Update election status"""
        try:
            for election in self.mock_elections:
                if election['id'] == election_id:
                    election['status'] = status
                    return True, f"Election status updated to {status}", election
            
            return False, "Election not found", None
        except Exception as e:
            return False, f"Error updating election status: {str(e)}", None
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {
                'total_elections': len(self.mock_elections),
                'active_elections': len([e for e in self.mock_elections if e['status'] == 'active']),
                'total_voters': len(self.mock_voters),
                'total_votes': len(self.mock_votes),
                'database_status': 'Connected (Mock)' if not self.db_available else 'Connected (Real)',
                'last_updated': datetime.now().isoformat()
            }
            
            return True, "Database stats retrieved", stats
        except Exception as e:
            return False, f"Error retrieving database stats: {str(e)}", {}

if __name__ == "__main__":
    db_connector = DatabaseConnector()
    success, message, elections = db_connector.get_elections()
    print(f"Test: {message}, Elections: {len(elections) if elections else 0}")
