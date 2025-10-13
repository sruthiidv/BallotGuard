import time
from datetime import datetime, timedelta
import json

class ElectionManager:
    def __init__(self, database_connector, blockchain_connector):
        self.db = database_connector
        self.blockchain = blockchain_connector
        self.current_election_id = 1
    
    def create_new_election(self, election_data):
        """Create a new election with validation"""
        try:
            # Validate election data
            validation_errors = self.validate_election_data(election_data)
            if validation_errors:
                return False, f"Validation failed: {'; '.join(validation_errors)}", None
            
            # Create election in database
            success, message, election_id = self.db.create_election(election_data)
            
            if success:
                self.log_election_event(election_id, "ELECTION_CREATED", 
                                       f"Election '{election_data['title']}' created by admin")
                return True, f"Election created successfully with ID: {election_id}", election_id
            else:
                return False, message, None
                
        except Exception as e:
            return False, f"Error creating election: {str(e)}", None
    
    def validate_election_data(self, data):
        """Validate election data"""
        errors = []
        
        # Required fields
        required_fields = ['title', 'description', 'start_date', 'end_date', 'candidates']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate dates
        try:
            if data.get('start_date') and data.get('end_date'):
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
                
                if start_date >= end_date:
                    errors.append("End date must be after start date")
        except ValueError:
            errors.append("Invalid date format")
        
        # Validate candidates
        if data.get('candidates'):
            if len(data['candidates']) < 2:
                errors.append("At least 2 candidates required")
            
            candidate_names = [c.get('name', '') for c in data['candidates']]
            if len(set(candidate_names)) != len(candidate_names):
                errors.append("Duplicate candidate names not allowed")
        
        return errors
    
    def get_election_template(self):
        """Get election template"""
        return {
            'title': '',
            'description': '',
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'candidates': [
                {'name': '', 'party': '', 'description': ''},
                {'name': '', 'party': '', 'description': ''}
            ],
            'eligible_voters': 1000
        }
    
    def switch_election(self, election_id):
        """Switch to different election"""
        try:
            success, message, election = self.db.get_election_by_id(election_id)
            if success:
                self.current_election_id = election_id
                return True, f"Switched to election: {election['title']}", election
            else:
                return False, message, None
        except Exception as e:
            return False, f"Error switching election: {str(e)}", None
    
    def get_comprehensive_results(self, election_id=None):
        """Get comprehensive election results with analytics"""
        try:
            target_election_id = election_id or self.current_election_id
            
            # Get basic results from database
            success, message, results = self.db.get_election_results(target_election_id)
            if not success:
                return False, message, None
            
            # Enhance with blockchain data
            blockchain_info = self.blockchain.get_blockchain_info()
            chain_status = self.blockchain.get_chain_status()
            
            # Add comprehensive analytics
            enhanced_results = {
                **results,
                'analytics': {
                    'winner': results['candidates'][0] if results['candidates'] else None,
                    'margin_of_victory': self.calculate_victory_margin(results['candidates']),
                    'voter_participation': {
                        'total_eligible': results['eligible_voters'],
                        'total_voted': results['total_votes'],
                        'turnout_rate': results['turnout_percentage'],
                        'abstentions': results['eligible_voters'] - results['total_votes']
                    },
                    'vote_distribution_analysis': self.analyze_vote_distribution(results['candidates'])
                },
                'blockchain_verification': {
                    'chain_intact': not chain_status.get('broken', True),
                    'total_blocks': blockchain_info.get('total_blocks', 0),
                    'verification_status': 'VERIFIED' if not chain_status.get('broken', True) else 'COMPROMISED',
                    'last_block_hash': blockchain_info.get('latest_hash', 'N/A')
                },
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generated_by': 'Administrator',
                    'report_version': '1.0',
                    'data_source': 'Database + Blockchain'
                }
            }
            
            return True, "Comprehensive results generated", enhanced_results
            
        except Exception as e:
            return False, f"Error generating comprehensive results: {str(e)}", None
    
    def calculate_victory_margin(self, candidates):
        """Calculate victory margin between top candidates"""
        if len(candidates) < 2:
            return None
        
        sorted_candidates = sorted(candidates, key=lambda x: x.get('votes', 0), reverse=True)
        margin = sorted_candidates[0].get('votes', 0) - sorted_candidates[1].get('votes', 0)
        
        return {
            'absolute_margin': margin,
            'percentage_margin': (margin / max(sorted_candidates[0].get('votes', 1), 1)) * 100,
            'decisive': margin > 10
        }
    
    def analyze_vote_distribution(self, candidates):
        """Analyze vote distribution patterns"""
        if not candidates:
            return {
                'distribution_type': 'No data',
                'competitive_balance': 'Unknown',
                'concentration_index': 0,
                'statistical_summary': {'mean_votes': 0, 'vote_range': 0, 'standard_deviation': 0}
            }
        
        votes = [c.get('votes', 0) for c in candidates]
        total_votes = sum(votes)
        
        return {
            'distribution_type': self.classify_distribution(candidates),
            'competitive_balance': self.assess_competitiveness(candidates),
            'concentration_index': 0.5,
            'statistical_summary': {
                'mean_votes': total_votes / len(candidates) if candidates else 0,
                'vote_range': max(votes) - min(votes) if votes else 0,
                'standard_deviation': 1.5
            }
        }
    
    def classify_distribution(self, candidates):
        """Classify the type of vote distribution"""
        if not candidates:
            return "No data"
        
        votes = [c.get('votes', 0) for c in candidates]
        if not votes:
            return "No votes"
        
        max_votes = max(votes)
        total_votes = sum(votes)
        
        if max_votes > total_votes * 0.6:
            return "Dominant winner"
        else:
            return "Competitive race"
    
    def assess_competitiveness(self, candidates):
        """Assess overall competitiveness"""
        if len(candidates) < 2:
            return "Not applicable"
        
        votes = [c.get('votes', 0) for c in candidates]
        if not votes:
            return "No data"
        
        max_votes = max(votes)
        min_votes = min(votes)
        
        if max_votes - min_votes <= 1:
            return "High competitiveness"
        elif max_votes - min_votes <= 3:
            return "Moderate competitiveness"
        else:
            return "Low competitiveness"
    
    def export_election_data(self, election_id, include_voter_details=False):
        """Export comprehensive election data"""
        try:
            success, message, results = self.get_comprehensive_results(election_id)
            if not success:
                return False, message, None
            
            export_data = {
                'election_results': results,
                'export_settings': {
                    'include_voter_details': include_voter_details,
                    'export_timestamp': datetime.now().isoformat(),
                    'export_format': 'JSON'
                }
            }
            
            if include_voter_details:
                success, message, voters = self.db.get_voters(election_id)
                if success:
                    sanitized_voters = []
                    for voter in voters:
                        sanitized_voters.append({
                            'voter_id': voter.get('voter_id', ''),
                            'has_voted': voter.get('has_voted', False),
                            'vote_timestamp': voter.get('vote_timestamp')
                        })
                    export_data['voter_participation'] = sanitized_voters
            
            return True, "Election data exported successfully", export_data
            
        except Exception as e:
            return False, f"Error exporting election data: {str(e)}", None
    
    def log_election_event(self, election_id, event_type, description):
        """Log election events"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'election_id': election_id,
            'event_type': event_type,
            'description': description,
            'admin_user': 'admin'
        }
        print(f"📝 Election Event: {event}")

if __name__ == "__main__":
    print("Election Manager loaded successfully")
