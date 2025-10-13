from flask import Flask
from flask_cors import CORS
from server_backend.database import db
from server_backend.routes import api_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    # --- Database config ---
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ballotguard.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
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
