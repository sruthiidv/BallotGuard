# ... (Existing imports and class structure)

class ElectionManager:
    def __init__(self, database_connector, blockchain_connector):
        self.db = database_connector
        self.blockchain = blockchain_connector
        self.current_election_id = 1
    
    # ... (Existing methods: create_new_election, validate_election_data, get_election_template, switch_election, get_comprehensive_results, calculate_victory_margin, analyze_vote_distribution, classify_distribution, assess_competitiveness, export_election_data, log_election_event)

    def delete_election(self, election_id):
        """Delete an election from the database and log the event."""
        try:
            # Check if election exists (optional, but good practice)
            success, message, election = self.db.get_election_by_id(election_id)
            if not success:
                return False, f"Deletion failed: {message}"
            
            # Attempt to delete
            success, message = self.db.delete_election(election_id)
            
            if success:
                self.log_election_event(election_id, "ELECTION_DELETED", 
                                       f"Election '{election.get('title', 'Unknown Title')}' (ID: {election_id}) deleted by admin")
                return True, f"Election ID {election_id} deleted successfully"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error deleting election: {str(e)}"

# ... (Existing main block)