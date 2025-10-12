from flask import Blueprint, jsonify

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/test", methods=["GET"])
def test_admin():
    return jsonify({
        "message": "Admin panel is working!",
        "status": "success",
        "endpoint": "/admin/test"
    })

@admin_bp.route("/tally", methods=["GET"])
def tally():
    return jsonify({
        "total_votes": 0,
        "message": "Database integration pending - Person 2's work",
        "status": "success"
    })
