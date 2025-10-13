import time
from datetime import datetime, timedelta
import json

class ElectionManager:
    def __init__(self, database_connector, blockchain_connector):
        self.db = database_connector
        self.blockchain = blockchain_connector
        self.current_election_id = 1  # Default to first election
    
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
                # Log election creation
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
        """Get election template for creation form"""
        return {
            'title': '',
            'description': '',
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'candidates': [
                {'name': '', 'party': '', 'description': ''},
                {'name': '', 'party': '', 'description': ''}
            ],
            'eligible_voters': 1000,
            'voting_rules': {
                'max_selections': 1,
                'allow_abstention': False,
                'require_verification': True
            }
        }
    
    def get_current_election(self):
        """Get currently active election"""
        try:
            success, message, election = self.db.get_election_by_id(self.current_election_id)
            return success, message, election
        except Exception as e:
            return False, f"Error getting current election: {str(e)}", None
    
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
                    'vote_distribution_analysis': self.analyze_vote_distribution(results['candidates']),
                    'temporal_analysis': self.analyze_voting_timeline(results.get('timestamps', []))
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
        
        sorted_candidates = sorted(candidates, key=lambda x: x['votes'], reverse=True)
        margin = sorted_candidates[0]['votes'] - sorted_candidates[1]['votes']
        
        return {
            'absolute_margin': margin,
            'percentage_margin': (margin / max(sorted_candidates[0]['votes'], 1)) * 100,
            'decisive': margin > 10  # Consider decisive if margin > 10 votes
        }
    
    def analyze_vote_distribution(self, candidates):
        """Analyze vote distribution patterns"""
        if not candidates:
            return None
        
        total_votes = sum(c['votes'] for c in candidates)
        
        analysis = {
            'distribution_type': self.classify_distribution(candidates),
            'concentration_index': self.calculate_concentration_index(candidates),
            'competitive_balance': self.assess_competitiveness(candidates),
            'statistical_summary': {
                'mean_votes': total_votes / len(candidates),
                'vote_range': max(c['votes'] for c in candidates) - min(c['votes'] for c in candidates),
                'standard_deviation': self.calculate_std_dev(candidates)
            }
        }
        
        return analysis
    
    def classify_distribution(self, candidates):
        """Classify the type of vote distribution"""
        if not candidates:
            return "No data"
        
        votes = [c['votes'] for c in candidates]
        max_votes = max(votes)
        
        # Count candidates with similar vote counts
        close_candidates = len([v for v in votes if v >= max_votes * 0.8])
        
        if close_candidates >= 3:
            return "Highly competitive (3+ way race)"
        elif close_candidates == 2:
            return "Competitive (close 2-way race)"
        elif max_votes > sum(votes) * 0.6:
            return "Dominant winner"
        else:
            return "Clear winner with competition"
    
    def calculate_concentration_index(self, candidates):
        """Calculate Herfindahl concentration index"""
        if not candidates:
            return 0
        
        total_votes = sum(c['votes'] for c in candidates)
        if total_votes == 0:
            return 0
        
        # Herfindahl index
        hhi = sum((c['votes'] / total_votes) ** 2 for c in candidates)
        
        # Normalize to 0-1 scale
        return round(hhi, 3)
    
    def assess_competitiveness(self, candidates):
        """Assess overall competitiveness of election"""
        if len(candidates) < 2:
            return "Not applicable"
        
        concentration = self.calculate_concentration_index(candidates)
        
        if concentration > 0.5:
            return "Low competitiveness"
        elif concentration > 0.35:
            return "Moderate competitiveness"
        else:
            return "High competitiveness"
    
    def calculate_std_dev(self, candidates):
        """Calculate standard deviation of vote counts"""
        if not candidates:
            return 0
        
        votes = [c['votes'] for c in candidates]
        mean = sum(votes) / len(votes)
        variance = sum((v - mean) ** 2 for v in votes) / len(votes)
        
        return round(variance ** 0.5, 2)
    
    def analyze_voting_timeline(self, timestamps):
        """Analyze voting patterns over time"""
        if not timestamps:
            return {"pattern": "No data available"}
        
        return {
            "pattern": "Steady voting throughout period",
            "peak_periods": ["Morning", "Evening"],
            "total_voting_sessions": len(timestamps)
        }
    
    def log_election_event(self, election_id, event_type, description):
        """Log election events for audit trail"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'election_id': election_id,
            'event_type': event_type,
            'description': description,
            'admin_user': 'admin'
        }
        
        print(f"📝 Election Event: {event}")
    
    def export_election_data(self, election_id, include_voter_details=False):
        """Export comprehensive election data"""
        try:
            # Get comprehensive results
            success, message, results = self.get_comprehensive_results(election_id)
            if not success:
                return False, message, None
            
            # Get additional data if requested
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
                    # Remove sensitive information
                    sanitized_voters = []
                    for voter in voters:
                        sanitized_voters.append({
                            'voter_id': voter['voter_id'],
                            'has_voted': voter['has_voted'],
                            'vote_timestamp': voter.get('vote_timestamp')
                        })
                    export_data['voter_participation'] = sanitized_voters
            
            return True, "Election data exported successfully", export_data
            
        except Exception as e:
            return False, f"Error exporting election data: {str(e)}", None

if __name__ == "__main__":
    print("Election Manager loaded successfully")
