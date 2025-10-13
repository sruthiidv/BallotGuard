from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import hashlib
import json
import time

# Initialize database
db = SQLAlchemy()

# Database Models
class Election(db.Model):
    __tablename__ = 'elections'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')
    eligible_voters = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), default='admin')
    
    # Relationships
    candidates = db.relationship('Candidate', backref='election', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='election', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status,
            'eligible_voters': self.eligible_voters,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'total_votes': len(self.votes),
            'candidates': [candidate.to_dict() for candidate in self.candidates]
        }

class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(100), default='Independent')
    description = db.Column(db.Text)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('Vote', backref='candidate', lazy=True)
    
    def to_dict(self):
        vote_count = Vote.query.filter_by(candidate_id=self.id).count()
        total_votes = Vote.query.filter_by(election_id=self.election_id).count()
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        
        return {
            'id': self.id,
            'name': self.name,
            'party': self.party,
            'description': self.description,
            'election_id': self.election_id,
            'votes': vote_count,
            'percentage': round(percentage, 2)
        }

class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    blockchain_hash = db.Column(db.String(64))
    
    __table_args__ = (db.UniqueConstraint('voter_id', 'election_id', name='unique_voter_election'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'voter_id': self.voter_id,
            'candidate_id': self.candidate_id,
            'election_id': self.election_id,
            'timestamp': self.timestamp.isoformat(),
            'blockchain_hash': self.blockchain_hash
        }

class Voter(db.Model):
    __tablename__ = 'voters'
    
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    vote_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'voter_id': self.voter_id,
            'name': self.name,
            'email': self.email,
            'has_voted': self.has_voted,
            'vote_timestamp': self.vote_timestamp.isoformat() if self.vote_timestamp else None,
            'created_at': self.created_at.isoformat()
        }

class BlockchainRecord(db.Model):
    __tablename__ = 'blockchain_records'
    
    id = db.Column(db.Integer, primary_key=True)
    block_index = db.Column(db.Integer, nullable=False)
    block_hash = db.Column(db.String(64), nullable=False)
    previous_hash = db.Column(db.String(64))
    vote_hash = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'block_index': self.block_index,
            'block_hash': self.block_hash,
            'previous_hash': self.previous_hash,
            'vote_hash': self.vote_hash,
            'timestamp': self.timestamp.isoformat()
        }

# Simple Blockchain Implementation
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

class SimpleBlockchain:
    def __init__(self):
        self.chain = []
        self.blockchain_file = "blockchain.json"
        self.load_chain()
        
        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), "Genesis Block", "0")
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
                timestamp=time.time(),
                vote_hash=vote_hash,
                previous_hash=latest_block.hash if latest_block else "0"
            )
            
            self.chain.append(new_block)
            self.save_chain()
            
            return True, new_block.hash
            
        except Exception as e:
            return False, str(e)

    def verify_chain(self):
        """Verify blockchain integrity"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False, f"Invalid hash at block {i}"
            
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

def create_sample_data():
    """Create sample election data"""
    try:
        print("🔄 Creating sample data...")
        
        # Create sample election
        election = Election(
            title="Student Council Election 2024",
            description="Annual student council election",
            start_date=datetime.now(),
            end_date=datetime.now(),
            status="active",
            eligible_voters=1000
        )
        db.session.add(election)
        db.session.flush()
        
        print(f"📊 Created election: {election.title} (ID: {election.id})")
        
        # Create candidates
        candidates_data = [
            {"name": "Alice Johnson", "party": "Progressive Party"},
            {"name": "Bob Smith", "party": "Conservative Party"},
            {"name": "Carol Davis", "party": "Independent"}
        ]
        
        candidates = []
        for cand_data in candidates_data:
            candidate = Candidate(
                name=cand_data["name"],
                party=cand_data["party"],
                election_id=election.id
            )
            candidates.append(candidate)
            db.session.add(candidate)
        
        db.session.flush()
        print(f"👥 Created {len(candidates)} candidates")
        
        # Create sample voters
        for i in range(1, 11):
            voter = Voter(
                voter_id=f"voter_{i:03d}",
                name=f"Voter {i}",
                email=f"voter{i}@example.com",
                has_voted=i <= 7
            )
            db.session.add(voter)
        
        db.session.flush()
        print(f"🗳️ Created 10 voters")
        
        # Create sample votes (Alice=3, Bob=2, Carol=2)
        vote_pattern = [0, 1, 0, 2, 1, 0, 1]  # Indices into candidates array
        
        for i, candidate_index in enumerate(vote_pattern):
            vote = Vote(
                voter_id=f"voter_{i+1:03d}",
                candidate_id=candidates[candidate_index].id,
                election_id=election.id,
                timestamp=datetime.now(),
                blockchain_hash=f"hash_{i+1:08x}"
            )
            db.session.add(vote)
        
        db.session.commit()
        
        print(f"📊 Created {len(vote_pattern)} votes")
        print("📈 Vote distribution:")
        for i, candidate in enumerate(candidates):
            vote_count = len([v for v, c in enumerate(vote_pattern) if c == i])
            print(f"   • {candidate.name}: {vote_count} votes")
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.session.rollback()
        raise

def create_app():
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'ballotguard-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "ballotguard.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    
    # Initialize blockchain
    blockchain = SimpleBlockchain()
    
    # Create tables and sample data
    with app.app_context():
        try:
            print("🔄 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if data exists
            if Election.query.count() == 0:
                create_sample_data()
            else:
                election_count = Election.query.count()
                vote_count = Vote.query.count()
                voter_count = Voter.query.count()
                print(f"📊 Database already contains:")
                print(f"   • {election_count} elections")
                print(f"   • {vote_count} votes") 
                print(f"   • {voter_count} voters")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")

    # Main routes
    @app.route('/')
    def home():
        try:
            elections_count = Election.query.count()
            votes_count = Vote.query.count()
            voters_count = Voter.query.count()
            
            return {
                "message": "BallotGuard Server is running!",
                "status": "success",
                "database": "✅ Connected to SQLite",
                "elections": elections_count,
                "votes": votes_count,
                "voters": voters_count,
                "endpoints": {
                    "test_database": "/test-db",
                    "api_elections": "/api/elections",
                    "api_votes": "/api/votes",
                    "api_voters": "/api/voters",
                    "blockchain_info": "/blockchain/info",
                    "blockchain_blocks": "/blockchain/blocks"
                }
            }
        except Exception as e:
            return {
                "message": "BallotGuard Server is running!",
                "status": "error",
                "database": "❌ Database error",
                "error": str(e)
            }, 500
    
    @app.route('/test-db')
    def test_database():
        try:
            elections_count = Election.query.count()
            votes_count = Vote.query.count()
            voters_count = Voter.query.count()
            
            return {
                "database_status": "✅ Connected",
                "elections": elections_count,
                "votes": votes_count,
                "voters": voters_count,
                "database_file": app.config['SQLALCHEMY_DATABASE_URI'],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "database_status": "❌ Error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, 500

    # Blockchain routes
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

    # API Blueprint
    api_bp = Blueprint('api', __name__)

    @api_bp.route('/elections', methods=['GET'])
    def get_elections():
        """Get all elections"""
        try:
            elections = Election.query.all()
            return jsonify([election.to_dict() for election in elections])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/elections/<int:election_id>', methods=['GET'])
    def get_election(election_id):
        """Get specific election"""
        try:
            election = Election.query.get_or_404(election_id)
            return jsonify(election.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 404

    @api_bp.route('/elections', methods=['POST'])
    def create_election():
        """Create new election"""
        try:
            data = request.get_json()
            
            if not data.get('title'):
                return jsonify({'error': 'Title is required'}), 400
            
            if not data.get('candidates') or len(data.get('candidates', [])) < 2:
                return jsonify({'error': 'At least 2 candidates are required'}), 400
            
            # Create election
            election = Election(
                title=data['title'],
                description=data.get('description', ''),
                start_date=datetime.fromisoformat(data['start_date'].replace('Z', '+00:00')),
                end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')),
                eligible_voters=data.get('eligible_voters', 1000)
            )
            
            db.session.add(election)
            db.session.flush()
            
            # Create candidates
            for candidate_data in data.get('candidates', []):
                if not candidate_data.get('name'):
                    continue
                    
                candidate = Candidate(
                    name=candidate_data['name'],
                    party=candidate_data.get('party', 'Independent'),
                    description=candidate_data.get('description', ''),
                    election_id=election.id
                )
                db.session.add(candidate)
            
            db.session.commit()
            return jsonify(election.to_dict()), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @api_bp.route('/elections/<int:election_id>', methods=['PATCH'])
    def update_election(election_id):
        """Update election"""
        try:
            election = Election.query.get_or_404(election_id)
            data = request.get_json()
            
            if 'status' in data:
                election.status = data['status']
            if 'title' in data:
                election.title = data['title']
            if 'description' in data:
                election.description = data['description']
            
            db.session.commit()
            return jsonify(election.to_dict())
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @api_bp.route('/voters', methods=['GET'])
    def get_voters():
        """Get voters"""
        try:
            voters = Voter.query.all()
            return jsonify([voter.to_dict() for voter in voters])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/votes', methods=['GET'])
    def get_votes():
        """Get votes"""
        try:
            election_id = request.args.get('election_id')
            
            if election_id:
                votes = Vote.query.filter_by(election_id=election_id).all()
            else:
                votes = Vote.query.all()
            
            return jsonify([vote.to_dict() for vote in votes])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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
            db.session.flush()
            
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

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")
    print("✅ API routes registered successfully")

    return app

if __name__ == "__main__":
    try:
        print("🚀 Starting BallotGuard Server...")
        print("=" * 50)
        
        app = create_app()
        
        print("=" * 50)
        print("✅ Server initialized successfully!")
        print("🌐 Server running at: http://localhost:5000")
        print("🧪 Test database: http://localhost:5000/test-db")
        print("📊 API elections: http://localhost:5000/api/elections")
        print("🗳️ API votes: http://localhost:5000/api/votes")
        print("⛓️ Blockchain info: http://localhost:5000/blockchain/info")
        print("=" * 50)
        
        app.run(debug=True, port=5000, host='0.0.0.0')
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        exit(1)
