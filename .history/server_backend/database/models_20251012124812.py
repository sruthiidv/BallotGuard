from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Import db from app.py
from app import db

class Election(db.Model):
    __tablename__ = 'elections'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
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
    
    # Unique constraint to prevent double voting
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
