from flask import Flask, request, jsonify
import uuid
import time
import hashlib
import os
import sqlite3
from datetime import datetime

from server_backend.crypto import sha_utils
from server_backend.blockchain import blockchain as blockchain_mod

# Requirements:
# pip install face_recognition numpy pycryptodome
# Plus dlib for face_recognition (use prebuilt wheels on Windows)

import json, base64
import numpy as np
import face_recognition

from Crypto.PublicKey import RSA
from Crypto.Signature import pss

from Crypto.Hash import SHA256
from server.server_config import RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM, PAILLIER_N, PAILLIER_P, PAILLIER_Q

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

def get_db():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

@app.route('/elections', methods=['GET', 'POST'])
def election_endpoints():
    """Handle election endpoints"""
    if request.method == 'GET':
        """Get list of all elections"""
        return jsonify(ELECTIONS)
    else:
        """Create new election"""
        try:
            data = request.json
            election_id = f"EL-{str(uuid.uuid4())[:8].upper()}"
            
            new_election = {
                "election_id": election_id,
                "name": data["name"],
                "status": "draft",  # Always start in draft
                "start_date": data["start_date"],
                "end_date": data["end_date"],
                "candidates": [],  # Empty initially
                "election_salt": os.urandom(8).hex()  # Random salt for vote_hash
            }
            
            ELECTIONS.append(new_election)

            # Create genesis block for the new election
            block_obj = blockchain_mod.Block(
                index=0,
                timestamp=time.time(),
                vote_hash=sha_utils.compute_sha256_hex(f'GENESIS||{election_id}'),
                previous_hash="GENESIS"
            )
            
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO ledger_blocks (election_id, ledger_index, vote_hash, prev_hash, hash, ts) VALUES (?, ?, ?, ?, ?, ?)",
                     (election_id, 0, block_obj.vote_hash, block_obj.previous_hash, block_obj.hash, block_obj.timestamp))
            conn.commit()
            conn.close()

            return jsonify(new_election), 201
        except Exception as e:
            return jsonify({"error": {"code": "CREATE_FAILED", "message": str(e)}}), 500

@app.route('/elections/<election_id>', methods=['GET'])
def get_election(election_id):
    """Get election details"""
    for election in ELECTIONS:
        if election["election_id"] == election_id:
            return jsonify(election)
    return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

@app.route('/elections/<election_id>/<action>', methods=['POST'])
def election_action(election_id, action):
    """Handle election state changes"""
    valid_actions = {"open", "close", "pause", "resume", "tally"}
    if action not in valid_actions:
        return jsonify({"error": {"code": "INVALID_ACTION", "message": f"Action must be one of: {valid_actions}"}}), 400

    for election in ELECTIONS:
        if election["election_id"] == election_id:
            if action == "open":
                if election["status"] != "draft":
                    return jsonify({"error": {"code": "INVALID_STATE", "message": "Can only open draft elections"}}), 400
                election["status"] = "open"
            elif action == "close":
                if election["status"] != "open":
                    return jsonify({"error": {"code": "INVALID_STATE", "message": "Can only close open elections"}}), 400
                election["status"] = "closed"
            elif action == "pause":
                if election["status"] != "open":
                    return jsonify({"error": {"code": "INVALID_STATE", "message": "Can only pause open elections"}}), 400
                election["status"] = "paused"
            elif action == "resume":
                if election["status"] != "paused":
                    return jsonify({"error": {"code": "INVALID_STATE", "message": "Can only resume paused elections"}}), 400
                election["status"] = "open"
            elif action == "tally":
                if election["status"] != "closed":
                    return jsonify({"error": {"code": "INVALID_STATE", "message": "Can only tally closed elections"}}), 400
                # Here we would decrypt votes using Paillier and compute totals
                return jsonify({"status": "completed", "message": "Tally generated"})
            
            return jsonify({"status": election["status"]})
            
    return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

@app.route('/voters', methods=['GET']) 
def get_voters():
    """Get list of all voters with their status"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM voters")
    voters = []
    for row in c.fetchall():
        voter = {
            "voter_id": row["voter_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "eligible_elections": []
        }
        # Get eligible elections
        c.execute("SELECT election_id FROM voter_election_status WHERE voter_id=? AND status='active'", (row["voter_id"],))
        voter["eligible_elections"] = [r["election_id"] for r in c.fetchall()]
        voters.append(voter)
    conn.close()
    return jsonify(voters)

@app.route('/voters/<voter_id>/block', methods=['POST'])
def block_voter(voter_id):
    """Block a voter"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE voters SET status='blocked' WHERE voter_id=?", (voter_id,))
    # Also update all election status records
    c.execute("UPDATE voter_election_status SET status='blocked' WHERE voter_id=?", (voter_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "blocked"})

@app.route('/ledger/verify', methods=['GET'])
def verify_ledger():
    """Verify ledger for an election"""
    election_id = request.args.get('election_id')
    if not election_id:
        return jsonify({"error": {"code": "MISSING_PARAM", "message": "election_id required"}}), 400

    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get all blocks for election
        c.execute("SELECT * FROM ledger_blocks WHERE election_id=? ORDER BY ledger_index", (election_id,))
        blocks = c.fetchall()
        
        if not blocks:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "No ledger found for election"}}), 404

        # Verify hash chain
        verification = {
            "election_id": election_id,
            "block_count": len(blocks),
            "chain_valid": True,
            "issues": []
        }

        prev_hash = "GENESIS"
        for block in blocks:
            # Recreate block object to verify hash
            block_obj = blockchain_mod.Block(
                index=block["ledger_index"],
                timestamp=block["ts"],
                vote_hash=block["vote_hash"],
                previous_hash=block["prev_hash"]
            )
            
            # Check hash chain continuity
            if block["prev_hash"] != prev_hash:
                verification["chain_valid"] = False
                verification["issues"].append(f"Break in hash chain at block {block['ledger_index']}")
            
            # Verify block hash
            if block["hash"] != block_obj.hash:
                verification["chain_valid"] = False
                verification["issues"].append(f"Invalid block hash at block {block['ledger_index']}")
            
            prev_hash = block["hash"]
        
        conn.close()
        return jsonify(verification)

    except Exception as e:
        return jsonify({"error": {"code": "VERIFY_FAILED", "message": str(e)}}), 500

# Voters endpoints (Admin)
@app.route('/voters/enroll', methods=['POST'])
def enroll_voter():
    """Enroll a new voter - MVP Architecture endpoint"""
    try:
        data = request.json
        
        # Generate unique voter ID
        voter_id = f"VOTER-{str(uuid.uuid4())[:8].upper()}"

        # Accept either face_encoding (preferred) or face_template (legacy), both as 128-float list
        face_encoding = data.get("face_encoding") or data.get("face_template")
        if not face_encoding:
            return jsonify({"error":{"code":"NO_FACE","message":"Provide 'face_encoding' (128 floats)."}}), 400
        try:
            enc = np.asarray(face_encoding, dtype=float).reshape(-1)
            if enc.shape[0] != 128:
                return jsonify({"error":{"code":"BAD_FACE_DIM","message":"face_encoding must be length 128."}}), 400
        except Exception as e:
            return jsonify({"error":{"code":"FACE_PARSE_FAIL","message":str(e)}}), 400

        VOTERS[voter_id] = {
            "voter_id": voter_id,
            "face_meta": enc.tolist(),  # 128-D vector
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

@app.route('/elections/<election_id>/proof', methods=['GET'])
def get_election_proof(election_id):
    """Get election proof bundle"""
    try:
        # Get election details
        election = next((e for e in ELECTIONS if e["election_id"] == election_id), None)
        if not election:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

        # Get ledger blocks
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM ledger_blocks WHERE election_id=? ORDER BY ledger_index", (election_id,))
        blocks = c.fetchall()

        # Get encrypted votes
        c.execute("SELECT * FROM encrypted_votes WHERE election_id=?", (election_id,))
        votes = c.fetchall()

        # Get redacted audit log
        c.execute("""
            SELECT action, election_id, ts 
            FROM audit_log 
            WHERE election_id=? 
            ORDER BY ts""", (election_id,))
        audit_log = c.fetchall()

        conn.close()

        # Bundle all proof materials
        proof_bundle = {
            "election_id": election_id,
            "election_salt": election["election_salt"],
            "ledger_snapshot": [dict(b) for b in blocks],
            "encrypted_votes": [{"vote_id": v["vote_id"], "ciphertext": v["ciphertext"]} for v in votes],
            "audit_log": [dict(e) for e in audit_log],  # PII redacted
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "block_count": len(blocks),
                "vote_count": len(votes)
            }
        }
        
        return jsonify(proof_bundle)
        
    except Exception as e:
        return jsonify({"error": {"code": "PROOF_FAILED", "message": str(e)}}), 500

@app.route('/elections/<election_id>/archive', methods=['POST'])
def archive_election(election_id):
    """Archive an election (demo-only)"""
    try:
        election = next((e for e in ELECTIONS if e["election_id"] == election_id), None)
        if not election:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

        if election["status"] != "closed":
            return jsonify({"error": {"code": "INVALID_STATE", "message": "Can only archive closed elections"}}), 400

        election["status"] = "archived"
        
        # Add audit log entry
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO audit_log (action, election_id, ts) 
                    VALUES (?, ?, ?)""", 
                    ("election_archived", election_id, datetime.utcnow().timestamp()))
        conn.commit()
        conn.close()

        return jsonify({"status": "archived"})

    except Exception as e:
        return jsonify({"error": {"code": "ARCHIVE_FAILED", "message": str(e)}}), 500

@app.route('/elections/<election_id>/reset', methods=['POST'])
def reset_election(election_id):
    """Reset an election (demo-only)"""
    try:
        election = next((e for e in ELECTIONS if e["election_id"] == election_id), None)
        if not election:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

        # Reset election state
        election["status"] = "draft"
        
        # Clear votes and ledger blocks
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM encrypted_votes WHERE election_id=?", (election_id,))
        c.execute("DELETE FROM ledger_blocks WHERE election_id=? AND ledger_index > 0", (election_id,))  # Keep genesis
        
        # Reset voter election status
        c.execute("UPDATE voter_election_status SET voted_flag=0 WHERE election_id=?", (election_id,))
        
        # Add audit log entry
        c.execute("""INSERT INTO audit_log (action, election_id, ts) 
                    VALUES (?, ?, ?)""", 
                    ("election_reset", election_id, datetime.utcnow().timestamp()))
        conn.commit()
        conn.close()

        return jsonify({"status": "reset"})

    except Exception as e:
        return jsonify({"error": {"code": "RESET_FAILED", "message": str(e)}}), 500

@app.route('/ledger/last', methods=['GET'])
def get_last_block():
    """Get last block of election ledger"""
    election_id = request.args.get('election_id')
    if not election_id:
        return jsonify({"error": {"code": "MISSING_PARAM", "message": "election_id required"}}), 400

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT ledger_index as index, hash 
            FROM ledger_blocks 
            WHERE election_id=? 
            ORDER BY ledger_index DESC 
            LIMIT 1""", (election_id,))
        last_block = c.fetchone()
        conn.close()

        if not last_block:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "No ledger found for election"}}), 404

        return jsonify(dict(last_block))

    except Exception as e:
        return jsonify({"error": {"code": "QUERY_FAILED", "message": str(e)}}), 500

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
    """Face verification - real encoding match using face_recognition"""
    try:
        data = request.json
        voter_id = data.get("voter_id")
        election_id = data.get("election_id")
        probe_encoding = data.get("face_encoding") or data.get("face_template")

        if not voter_id or not probe_encoding:
            return jsonify({"error":{"code":"NO_DATA","message":"Missing voter_id or face_encoding"}}), 400

        if voter_id not in VOTERS:
            print(f"DEBUG: Face verify failed - unknown voter. voter_id={voter_id}")
            return jsonify({"error":{"code":"NOT_FOUND","message":"Voter not found"}}), 404

        voter = VOTERS[voter_id]
        if voter["status"] != "active":
            return jsonify({"error":{"code":"VOTER_INACTIVE","message":"Voter not approved"}}), 403

        ves_key = (election_id, voter_id)
        if ves_key not in VOTER_ELECTION_STATUS:
            return jsonify({"error":{"code":"NOT_ELIGIBLE","message":"Not eligible for this election"}}), 403

        if VOTER_ELECTION_STATUS[ves_key]["voted_flag"]:
            return jsonify({"error":{"code":"ALREADY_VOTED","message":"Already voted in this election"}}), 409

        try:
            stored = np.asarray(voter["face_meta"], dtype=float)
            probe = np.asarray(probe_encoding, dtype=float)
            matches = face_recognition.compare_faces([stored], probe, tolerance=0.5)
            distance = float(face_recognition.face_distance([stored], probe)[0])
            passed = bool(matches[0])
            confidence = max(0.0, 1.0 - distance)  # heuristic
        except Exception as e:
            return jsonify({"error":{"code":"FACE_COMPARE_FAIL","message":str(e)}}), 500

        VOTER_ELECTION_STATUS[ves_key]["last_auth_ts"] = time.time()
        print(f"DEBUG: Face verify {'PASS' if passed else 'FAIL'}. voter_id={voter_id}, election_id={election_id}, conf={confidence:.3f}")
        return jsonify({"pass": passed, "confidence": confidence, "voter_id": voter_id})
    except Exception as e:
        return jsonify({"error":{"code":"AUTH_FAIL","message":str(e)}}), 500

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
    print("   GET  /elections")
    print("   POST /voters/enroll")
    print("   POST /voters/<id>/approve")
    print("   POST /auth/face/verify")
    print("   POST /ovt/issue")
    print("   POST /votes")
    print("   GET  /health")
    print("-" * 50)
    app.run(host='127.0.0.1', port=8443, debug=True)