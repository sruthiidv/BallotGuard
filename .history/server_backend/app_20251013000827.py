from flask import Flask
from flask_cors import CORS
from database import db  # your SQLAlchemy instance from database/__init__.py
from routes import api_bp  # import your Blueprint from routes.py

def create_app():
    app = Flask(__name__)
    CORS(app)

    # --- Database configuration ---
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ballotguard.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize DB
    db.init_app(app)

    # Register routes
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route('/')
    def home():
        return {"message": "BallotGuard Flask API is running"}

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
