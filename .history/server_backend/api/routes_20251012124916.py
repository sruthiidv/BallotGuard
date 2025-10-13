from flask import Blueprint, request, jsonify
from database.models import db, Election, Candidate, Vote, Voter
from datetime import datetime

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
        
        # Create election
        election = Election(
            title=data['title'],
            description=data.get('description', ''),
            start_date=datetime.fromisoformat(data['start_date'].replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')),
            eligible_voters=data.get('eligible_voters', 1000)
        )
        
        db.session.add(election)
        db.session.flush()  # Get election ID
        
        # Create candidates
        for candidate_data in data.get('candidates', []):
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
