from flask import Flask, request, jsonify
import uuid
import time
import hashlib
from datetime import datetime

app = Flask(__name__)
from client_app.crypto.vote_crypto import prepare_vote_data, generate_vote_id
from server_backend.crypto.ovt import generate_ovt, sign_ovt
from server_backend.crypto.ledger_crypto import create_block_header, sign_block_header
from client_app.storage.localdb import (
    init as db_init, store_ovt, is_ovt_used,
    store_vote, store_receipt, mark_ovt_used, fetch_last_receipt
)
from server_backend.crypto.sha_utils import compute_sha256_hex

DB_PATH = "client_local.db"
db_init(DB_PATH)  # Initialize local DB
print("✅ Local DB initialized.")
# Simple in-memory storage - matching MVP Architecture
ELECTIONS = [
    {
        "election_id": "EL-2025-01",
        "name": "City Council Election 2025",
        "status": "open",
        "start_date": "2025-10-01",
        "end_date": "2025-10-31",
        "candidates": [
            {"candidate_id": "C1", "name": "Alice Johnson", "party": "Progressive Party"},
            {"candidate_id": "C2", "name": "Bob Smith", "party": "Conservative Party"},
            {"candidate_id": "C3", "name": "Charlie Brown", "party": "Independent"}
        ],
        "election_salt": "f00dbabe"  # For vote_hash computation
    },
    {
        "election_id": "EL-2025-02", 
        "name": "School Board Election 2025",
        "status": "open",
        "start_date": "2025-10-05",
        "end_date": "2025-10-25",
        "candidates": [
            {"candidate_id": "C1", "name": "David Miller", "party": "Education First"},
            {"candidate_id": "C2", "name": "Emma Davis", "party": "Parent Coalition"}
        ],
        "election_salt": "cafebabe"
    },
    {
        "election_id": "EL-2025-03",
        "name": "Library Board Election 2025", 
        "status": "open",
        "start_date": "2025-10-10",
        "end_date": "2025-11-10",
        "candidates": [
            {"candidate_id": "C1", "name": "Frank Wilson", "party": "Independent"},
            {"candidate_id": "C2", "name": "Grace Lee", "party": "Independent"}
        ],
        "election_salt": "deadbeef"
    }
]

# MVP Architecture Data Structures
VOTERS = {}  # voter_id -> {voter_id, face_meta, status, created_at}
VOTER_ELECTION_STATUS = {}  # (election_id, voter_id) -> {status, voted_flag, last_auth_ts}
OVT_TOKENS = {}  # ovt_uuid -> {ovt_uuid, election_id, voter_id, status, expires_at, issued_ts}
ENCRYPTED_VOTES = {}  # vote_id -> {vote_id, election_id, ciphertext, client_hash, ledger_index, ts}
LEDGER_BLOCKS = {}  # (election_id, index) -> {index, election_id, vote_hash, prev_hash, hash, ts}

# Counters for ledger indices per election
LEDGER_INDICES = {election["election_id"]: 0 for election in ELECTIONS}

# MVP Architecture Endpoints

@app.route('/elections', methods=['GET'])
def get_elections():
    """Get list of all elections"""
    return jsonify(ELECTIONS)

# Voters endpoints (Admin)
@app.route('/voters/enroll', methods=['POST'])
def enroll_voter():
    """Enroll a new voter - MVP Architecture endpoint"""
    try:
        data = request.json
        
        # Generate unique voter ID
        voter_id = f"VOTER-{str(uuid.uuid4())[:8].upper()}"
        
        # Store voter data
        VOTERS[voter_id] = {
            "voter_id": voter_id,
            "face_meta": data.get("face_template"),  # Store face template as face_meta
            "status": "pending",
            "created_at": time.time()
        }
        
        # Auto-approve after 3 seconds (for demo)
        def auto_approve():
            time.sleep(3)
            if voter_id in VOTERS:
                VOTERS[voter_id]["status"] = "active"
                
                # Make voter eligible for all open elections
                for election in ELECTIONS:
                    if election["status"] == "open":
                        ves_key = (election["election_id"], voter_id)
                        VOTER_ELECTION_STATUS[ves_key] = {
                            "status": "active",
                            "voted_flag": False,
                            "last_auth_ts": None
                        }
        
        import threading
        threading.Thread(target=auto_approve, daemon=True).start()
        
        return jsonify({
            "voter_id": voter_id,
            "status": "pending"
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": {
                "code": "ENROLL_FAILED",
                "message": str(e)
            }
        }), 500

@app.route('/voters/<voter_id>/approve', methods=['POST'])
def approve_voter(voter_id):
    """Approve a voter - MVP Architecture endpoint"""
    if voter_id not in VOTERS:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Voter not found"
            }
        }), 404
    
    VOTERS[voter_id]["status"] = "active"
    
    # Make eligible for all open elections
    for election in ELECTIONS:
        if election["status"] == "open":
            ves_key = (election["election_id"], voter_id)
            VOTER_ELECTION_STATUS[ves_key] = {
                "status": "active", 
                "voted_flag": False,
                "last_auth_ts": None
            }
    
    return jsonify({"status": "active"})

# Auth & OVT endpoints (Booth)
@app.route('/auth/face/verify', methods=['POST'])
def verify_face():
    """Face verification - MVP Architecture endpoint"""
    try:
        data = request.json
        voter_id = data.get("voter_id")
        election_id = data.get("election_id")
        
        if voter_id not in VOTERS:
            return jsonify({
                "error": {
                    "code": "NOT_FOUND", 
                    "message": "Voter not found"
                }
            }), 404
        
        voter = VOTERS[voter_id]
        if voter["status"] != "active":
            return jsonify({
                "error": {
                    "code": "VOTER_INACTIVE",
                    "message": "Voter not approved"
                }
            }), 403
        
        # Check voter election status
        ves_key = (election_id, voter_id)
        if ves_key not in VOTER_ELECTION_STATUS:
            return jsonify({
                "error": {
                    "code": "NOT_ELIGIBLE",
                    "message": "Not eligible for this election"
                }
            }), 403
            
        ves = VOTER_ELECTION_STATUS[ves_key]
        if ves["voted_flag"]:
            return jsonify({
                "error": {
                    "code": "ALREADY_VOTED",
                    "message": "Already voted in this election"
                }
            }), 409
        
        # Update last auth timestamp
        ves["last_auth_ts"] = time.time()
        
        # For demo, always return success
        return jsonify({
            "pass": True,
            "confidence": 0.95,
            "voter_id": voter_id
        })
        
    except Exception as e:
        return jsonify({
            "error": {
                "code": "AUTH_FAIL",
                "message": str(e)
            }
        }), 500

@app.route('/ovt/issue', methods=['POST'])
def issue_ovt():
    try:
        data = request.json
        voter_id = data.get("voter_id")
        election_id = data.get("election_id")

        ves_key = (election_id, voter_id)
        if ves_key not in VOTER_ELECTION_STATUS:
            return jsonify({"error": {"code": "NOT_ELIGIBLE", "message": "Not eligible"}}), 403

        # Generate OVT and signature
        ovt_bytes = generate_ovt()
        server_sig_bytes = sign_ovt(ovt_bytes)
        ovt_token_str = ovt_bytes.hex()
        server_sig_str = server_sig_bytes.hex()

        # Store in DB
        store_ovt(ovt_token_str, election_id, DB_PATH)

        return jsonify({"ovt": {"token": ovt_token_str, "signature": server_sig_str}})

    except Exception as e:
        return jsonify({"error": {"code": "OVT_ISSUE_FAILED", "message": str(e)}}), 500


@app.route('/votes', methods=['POST'])
def cast_vote():
    try:
        data = request.json
        vote_id = data.get("vote_id")
        election_id = data.get("election_id")
        candidate_id = data.get("candidate_id")
        ovt = data.get("ovt", {})
        ovt_token_str = ovt.get("token")

        if not ovt_token_str:
            return jsonify({"error": "OVT missing"}), 400

        if is_ovt_used(ovt_token_str, DB_PATH):
            return jsonify({"error": "OVT already used"}), 409

        vote_id = vote_id or generate_vote_id()
        vote_data = prepare_vote_data(vote_id, election_id, candidate_id, ovt)
        ciphertext = str(vote_data)
        client_hash = compute_sha256_hex(ciphertext)

        last_index, last_hash = fetch_last_receipt(election_id, DB_PATH)
        block_header = create_block_header(last_index + 1, client_hash, last_hash)
        block_signature = sign_block_header(block_header)

        store_vote(vote_id, election_id, ciphertext, ovt_token_str, DB_PATH)
        store_receipt(vote_id, election_id, block_header["index"], client_hash, block_signature.hex(), DB_PATH)
        mark_ovt_used(ovt_token_str, DB_PATH)

        return jsonify({"ledger_index": block_header["index"], "block_hash": block_signature.hex(), "ack": "stored"})

    except Exception as e:
        return jsonify({"error": {"code": "VOTE_FAILED", "message": str(e)}}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "elections_count": len(ELECTIONS),
        "voters_count": len(VOTERS),
        "votes_count": len(ENCRYPTED_VOTES),
        "ovt_tokens_count": len(OVT_TOKENS)
    })

if __name__ == '__main__':
    print("🗳️  BallotGuard Dummy Server Starting...")
    print("📡 Server running on: http://127.0.0.1:8443")
    print("📋 Available endpoints:")
    print("   GET  /elections - List all elections")
    print("   POST /register - Register new voter")
    print("   GET  /voter/<id>/status - Check voter status") 
    print("   POST /verify - Verify voter face")
    print("   POST /vote - Cast vote")
    print("   GET  /health - Server health check")
    print("-" * 50)
    
    app.run(host='127.0.0.1', port=8443, debug=True)