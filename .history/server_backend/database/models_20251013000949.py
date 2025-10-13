from datetime import datetime
from . import db


class Election(db.Model):
    __tablename__ = 'elections'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, default=datetime.utcnow)
    eligible_voters = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='PENDING')

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "eligible_voters": self.eligible_voters,
            "status": self.status
        }


class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(100))
    description = db.Column(db.String(300))
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "party": self.party,
            "description": self.description,
            "election_id": self.election_id
        }


class Voter(db.Model):
    __tablename__ = 'voters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    voter_id = db.Column(db.String(50), unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "voter_id": self.voter_id
        }


class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "election_id": self.election_id,
            "candidate_id": self.candidate_id,
            "timestamp": self.timestamp.isoformat()
        }
