from flask import Blueprint, request, jsonify

api_bp = Blueprint("api_bp", __name__)

@api_bp.route("/test", methods=["GET"])
def test_api():
    return jsonify({
        "message": "API is working!",
        "status": "success",
        "endpoint": "/api/test"
    })

@api_bp.route("/submit_vote", methods=["POST"])
def submit_vote():
    try:
        data = request.get_json()
        
        # Basic validation
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        voter_id = data.get("voter_id")
        encrypted_vote = data.get("encrypted_vote")
        
        if not voter_id or not encrypted_vote:
            return jsonify({"error": "Missing voter_id or encrypted_vote"}), 400

        # Mock successful response (until Person 2 adds database/crypto)
        return jsonify({
            "message": "Vote recorded successfully",
            "voter_id": voter_id,
            "status": "success",
            "note": "Database integration pending - Person 2's work"
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "BallotGuard API"
    })
