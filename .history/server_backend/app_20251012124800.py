from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize database
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'ballotguard-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "ballotguard.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    
    # Import models here to avoid circular imports
    from database.models import Election, Candidate, Vote, Voter
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Add sample data if database is empty
        if Election.query.count() == 0:
            create_sample_data()
            print("✅ Sample data added to database")

    # Main route
    @app.route('/')
    def home():
        return {
            "message": "BallotGuard Server is running!",
            "status": "success",
            "database": "Connected to SQLite",
            "tables_count": len(db.metadata.tables)
        }
    
    # Database test route
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
                "database_file": app.config['SQLALCHEMY_DATABASE_URI']
            }
        except Exception as e:
            return {
                "database_status": "❌ Error",
                "error": str(e)
            }

    # Register blueprints
    try:
        from api.routes import api_bp
        app.register_blueprint(api_bp, url_prefix="/api")
        print("✅ API routes loaded successfully.")
    except ImportError as e:
        print(f"❌ Could not load API routes: {e}")

    try:
        from admin_panel.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix="/admin")
        print("✅ Admin panel routes loaded successfully.")
    except ImportError as e:
        print(f"❌ Could not load admin panel routes: {e}")

    return app

def create_sample_data():
    """Create sample election data"""
    try:
        from database.models import Election, Candidate, Vote, Voter
        
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
        db.session.flush()  # Get the ID
        
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
        
        db.session.flush()  # Get candidate IDs
        
        # Create sample voters
        for i in range(1, 11):
            voter = Voter(
                voter_id=f"voter_{i:03d}",
                name=f"Voter {i}",
                email=f"voter{i}@example.com",
                has_voted=i <= 7
            )
            db.session.add(voter)
        
        db.session.flush()  # Get voter IDs
        
        # Create sample votes
        vote_pattern = [0, 1, 0, 2, 1, 0, 1]  # Alice=3, Bob=2, Carol=1, rest=1
        
        for i, candidate_index in enumerate(vote_pattern):
            vote = Vote(
                voter_id=f"voter_{i+1:03d}",
                candidate_id=candidates[candidate_index].id,
                election_id=election.id,
                timestamp=datetime.now(),
                blockchain_hash=f"hash_{i+1}"
            )
            db.session.add(vote)
        
        db.session.commit()
        print("✅ Sample data created successfully")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.session.rollback()

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
