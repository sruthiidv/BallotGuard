from flask import Flask
from flask_cors import CORS
from database import db  # Import db from database/__init__.py
from datetime import datetime
import os

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
    
    # Import models AFTER db.init_app()
    from database.models import Election, Candidate, Vote, Voter
    
    # Create tables and add sample data
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Add sample data if database is empty
            if Election.query.count() == 0:
                create_sample_data()
                print("✅ Sample data added to database")
            else:
                print("📊 Database already has data")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")

    # Main route
    @app.route('/')
    def home():
        try:
            from database.models import Election, Vote, Voter
            elections_count = Election.query.count()
            votes_count = Vote.query.count()
            voters_count = Voter.query.count()
            
            return {
                "message": "BallotGuard Server is running!",
                "status": "success",
                "database": "Connected to SQLite",
                "elections": elections_count,
                "votes": votes_count,
                "voters": voters_count,
                "database_file": app.config['SQLALCHEMY_DATABASE_URI']
            }
        except Exception as e:
            return {
                "message": "BallotGuard Server is running!",
                "status": "error",
                "database_error": str(e)
            }
    
    # Database test route
    @app.route('/test-db')
    def test_database():
        try:
            from database.models import Election, Vote, Voter
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
            }, 500

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
        
        print(f"📊 Created election with ID: {election.id}")
        
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
        print(f"👥 Created {len(candidates)} candidates")
        
        # Create sample voters
        voters = []
        for i in range(1, 11):
            voter = Voter(
                voter_id=f"voter_{i:03d}",
                name=f"Voter {i}",
                email=f"voter{i}@example.com",
                has_voted=i <= 7
            )
            voters.append(voter)
            db.session.add(voter)
        
        db.session.flush()  # Get voter IDs
        print(f"🗳️ Created {len(voters)} voters")
        
        # Create sample votes
        vote_pattern = [0, 1, 0, 2, 1, 0, 1]  # Alice=3, Bob=2, Carol=1, rest=1
        
        votes = []
        for i, candidate_index in enumerate(vote_pattern):
            vote = Vote(
                voter_id=f"voter_{i+1:03d}",
                candidate_id=candidates[candidate_index].id,
                election_id=election.id,
                timestamp=datetime.now(),
                blockchain_hash=f"hash_{i+1}"
            )
            votes.append(vote)
            db.session.add(vote)
        
        db.session.commit()
        print(f"📊 Created {len(votes)} votes")
        print("✅ Sample data created successfully")
        
        # Print vote distribution
        for i, candidate in enumerate(candidates):
            vote_count = len([v for v in votes if v.candidate_id == candidate.id])
            print(f"   {candidate.name}: {vote_count} votes")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    try:
        print("🚀 Starting BallotGuard Server...")
        app = create_app()
        print("✅ Server initialized successfully")
        print("🌐 Server will be available at: http://localhost:5000")
        print("🧪 Database test endpoint: http://localhost:5000/test-db")
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
