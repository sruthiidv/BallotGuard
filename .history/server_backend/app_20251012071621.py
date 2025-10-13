from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'ballotguard-secret'
    CORS(app)

    # Main route
    @app.route('/')
    def home():
        return {
            "message": "BallotGuard Server is running!",
            "status": "success",
            "person_3_work": "Flask API structure complete"
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

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
