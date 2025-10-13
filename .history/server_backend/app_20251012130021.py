# Add blockchain integration
import hashlib
import json
import os
from datetime import datetime

class Block:
    def __init__(self, index, timestamp, vote_hash, previous_hash=""):
        self.index = index
        self.timestamp = timestamp
        self.vote_hash = vote_hash
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.vote_hash}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.blockchain_file = "blockchain.json"
        self.load_chain()
        
        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, datetime.now().timestamp(), "Genesis Block", "0")
        self.chain.append(genesis_block)
        self.save_chain()

    def get_latest_block(self):
        return self.chain[-1] if self.chain else None

    def add_vote_block(self, vote_data):
        """Add vote to blockchain"""
        try:
            vote_string = f"{vote_data['voter_id']}_{vote_data['candidate_id']}_{vote_data['election_id']}_{vote_data['timestamp']}"
            vote_hash = hashlib.sha256(vote_string.encode()).hexdigest()
            
            latest_block = self.get_latest_block()
            new_block = Block(
                index=len(self.chain),
                timestamp=datetime.now().timestamp(),
                vote_hash=vote_hash,
                previous_hash=latest_block.hash if latest_block else "0"
            )
            
            self.chain.append(new_block)
            self.save_chain()
            
            # Also save to database
            blockchain_record = BlockchainRecord(
                block_index=new_block.index,
                block_hash=new_block.hash,
                previous_hash=new_block.previous_hash,
                vote_hash=new_block.vote_hash,
                timestamp=datetime.fromtimestamp(new_block.timestamp)
            )
            db.session.add(blockchain_record)
            db.session.commit()
            
            return True, new_block.hash
            
        except Exception as e:
            return False, str(e)

    def verify_chain(self):
        """Verify blockchain integrity"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False, f"Invalid hash at block {i}"
            
            # Check if current block's previous_hash matches previous block's hash
            if current_block.previous_hash != previous_block.hash:
                return False, f"Invalid previous hash at block {i}"
        
        return True, "Chain is valid"

    def save_chain(self):
        """Save blockchain to file"""
        try:
            chain_data = []
            for block in self.chain:
                chain_data.append({
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'vote_hash': block.vote_hash,
                    'previous_hash': block.previous_hash,
                    'hash': block.hash
                })
            
            with open(self.blockchain_file, 'w') as f:
                json.dump(chain_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving blockchain: {e}")

    def load_chain(self):
        """Load blockchain from file"""
        try:
            if os.path.exists(self.blockchain_file):
                with open(self.blockchain_file, 'r') as f:
                    chain_data = json.load(f)
                
                self.chain = []
                for block_data in chain_data:
                    block = Block(
                        block_data['index'],
                        block_data['timestamp'],
                        block_data['vote_hash'],
                        block_data['previous_hash']
                    )
                    block.hash = block_data['hash']
                    self.chain.append(block)
                    
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.chain = []

# Initialize blockchain
blockchain = Blockchain()

# Add blockchain routes
@app.route('/blockchain/info')
def blockchain_info():
    """Get blockchain information"""
    try:
        is_valid, message = blockchain.verify_chain()
        
        return {
            "total_blocks": len(blockchain.chain),
            "latest_hash": blockchain.get_latest_block().hash if blockchain.chain else None,
            "chain_valid": is_valid,
            "validation_message": message,
            "blockchain_file_exists": os.path.exists("blockchain.json")
        }
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/blockchain/blocks')
def get_blocks():
    """Get recent blockchain blocks"""
    try:
        blocks_data = []
        recent_blocks = blockchain.chain[-10:] if len(blockchain.chain) > 10 else blockchain.chain
        
        for block in recent_blocks:
            blocks_data.append({
                'index': block.index,
                'timestamp': datetime.fromtimestamp(block.timestamp).isoformat(),
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'vote_hash': block.vote_hash
            })
        
        return jsonify(blocks_data)
    except Exception as e:
        return {"error": str(e)}, 500

# Modify vote creation to include blockchain
@api_bp.route('/votes', methods=['POST'])
def create_vote():
    """Create vote and add to blockchain"""
    try:
        data = request.get_json()
        
        # Create vote in database
        vote = Vote(
            voter_id=data['voter_id'],
            candidate_id=data['candidate_id'],
            election_id=data['election_id'],
            timestamp=datetime.now()
        )
        db.session.add(vote)
        db.session.flush()  # Get vote ID
        
        # Add to blockchain
        vote_data = {
            'voter_id': vote.voter_id,
            'candidate_id': vote.candidate_id,
            'election_id': vote.election_id,
            'timestamp': vote.timestamp.isoformat()
        }
        
        success, blockchain_hash = blockchain.add_vote_block(vote_data)
        
        if success:
            vote.blockchain_hash = blockchain_hash
            db.session.commit()
            
            return jsonify({
                'vote': vote.to_dict(),
                'blockchain_hash': blockchain_hash,
                'message': 'Vote recorded in database and blockchain'
            }), 201
        else:
            db.session.rollback()
            return jsonify({'error': f'Failed to add to blockchain: {blockchain_hash}'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
