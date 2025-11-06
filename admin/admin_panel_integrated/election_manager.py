import time
from datetime import datetime, timedelta
import json

class ElectionManager:
    def __init__(self, database_connector, blockchain_connector):
        self.db = database_connector
        self.blockchain = blockchain_connector
        self.current_election_id = 1
    
    # ... (Existing methods: create_new_election, validate_election_data, etc.)

    # --- NEW: Delete Election Method ---
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
                # Log event only if deletion was successful
                election_title = election.get('title', 'Unknown Title')
                self.log_election_event(election_id, "ELECTION_DELETED", 
                                       f"Election '{election_title}' (ID: {election_id}) deleted by admin")
                return True, f"Election ID {election_id} deleted successfully"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error deleting election: {str(e)}"
            
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
        
    # ... (rest of the file is assumed to contain other methods or main block)