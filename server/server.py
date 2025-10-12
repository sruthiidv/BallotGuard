from flask import Flask, request, jsonify
import uuid
import time
import hashlib
from datetime import datetime

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

RSA_SK = RSA.import_key(RECEIPT_RSA_PRIV_PEM)
RSA_PUB_PEM = RECEIPT_RSA_PUB_PEM  # returned to clients for verification

@app.route('/public-key', methods=['GET'])
def get_public_key():
    return jsonify({"rsa_pub_pem": RSA_PUB_PEM})

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
    """Issue OVT token - MVP Architecture endpoint"""
    try:
        data = request.json
        voter_id = data.get("voter_id")
        election_id = data.get("election_id")
        
        # Validate voter and election eligibility
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
        
        # Revoke any existing unspent OVTs for this voter/election
        for ovt_uuid, ovt in OVT_TOKENS.items():
            if (ovt["voter_id"] == voter_id and 
                ovt["election_id"] == election_id and 
                ovt["status"] == "issued"):
                ovt["status"] = "expired"
        
        # Generate new OVT
        ovt_uuid = str(uuid.uuid4())
        expires_at = time.time() + 300  # 5 minutes TTL
        
        ovt = {
            "ovt_uuid": ovt_uuid,
            "election_id": election_id,
            "voter_id": voter_id,
            "not_before": time.time(),
            "expires_at": expires_at
        }
        
        # Store OVT
        OVT_TOKENS[ovt_uuid] = {
            "ovt_uuid": ovt_uuid,
            "election_id": election_id,
            "voter_id": voter_id,
            "status": "issued",
            "expires_at": expires_at,
            "issued_ts": time.time()
        }
        
        # Real RSA-PSS signature of the canonical OVT JSON
        ovt_bytes = json.dumps(ovt, sort_keys=True, separators=(",", ":")).encode()
        h = SHA256.new(ovt_bytes)
        sig = pss.new(RSA_SK).sign(h)
        server_sig = base64.b64encode(sig).decode()

        return jsonify({
            "ovt": ovt,
            "server_sig": server_sig  # client already knows RSA_PUB_PEM
        })
        
    except Exception as e:
        return jsonify({
            "error": {
                "code": "OVT_ISSUE_FAILED",
                "message": str(e)
            }
        }), 500

# Votes endpoint (Booth)
@app.route('/votes', methods=['POST'])
def cast_vote():
    """Cast a vote - MVP Architecture endpoint"""
    try:
        data = request.json
        vote_id = data.get("vote_id")
        election_id = data.get("election_id")
        candidate_id = data.get("candidate_id")
        ciphertext = data.get("ciphertext", "mock_encrypted_vote")
        client_hash = data.get("client_hash")
        ovt = data.get("ovt", {})
        ovt_uuid = ovt.get("ovt_uuid") if ovt else None
        
        # Validate OVT
        if not ovt_uuid or ovt_uuid not in OVT_TOKENS:
            return jsonify({"error": {"code": "OVT_NOT_FOUND","message": "Invalid or missing OVT"}}), 400

        ovt_token = OVT_TOKENS[ovt_uuid]
        if ovt_token["status"] != "issued":
            return jsonify({"error": {"code": "OVT_SPENT","message": "OVT already used"}}), 409

        if ovt_token["expires_at"] < time.time():
            return jsonify({"error": {"code": "OVT_EXPIRED", "message": "OVT expired"}}), 403

        if ovt_token["election_id"] != election_id:
            return jsonify({"error": {"code": "OVT_ELECTION_MISMATCH","message": "OVT not issued for this election"}}), 403

        voter_id = ovt_token["voter_id"]

        # Check if already voted
        ves_key = (election_id, voter_id)
        if ves_key in VOTER_ELECTION_STATUS:
            ves = VOTER_ELECTION_STATUS[ves_key]
            if ves["voted_flag"]:
                return jsonify({"error": {"code": "ALREADY_VOTED","message": "Already voted in this election"}}), 409

        # Check for duplicate vote_id (idempotency)
        if vote_id in ENCRYPTED_VOTES:
            # Return same response for idempotent replay
            existing_vote = ENCRYPTED_VOTES[vote_id]
            return jsonify({
                "ledger_index": existing_vote["ledger_index"],
                "block_hash": existing_vote.get("block_hash", "mock_hash"),
                "ack": "stored"
            })

        # Get election salt for vote_hash
        election_salt = "default_salt"
        for election in ELECTIONS:
            if election["election_id"] == election_id:
                election_salt = election.get("election_salt", "default_salt")
                break

        # Compute vote_hash (MVP Architecture)
        vote_hash = hashlib.sha256(f"{ciphertext}{election_salt}".encode()).hexdigest()

        # Get next ledger index
        ledger_index = LEDGER_INDICES[election_id]
        LEDGER_INDICES[election_id] += 1

        # Compute block hash
        prev_hash = "GENESIS" if ledger_index == 0 else LEDGER_BLOCKS[(election_id, ledger_index-1)]["hash"]
        block_data = f"{ledger_index}{election_id}{vote_hash}{prev_hash}"
        block_hash = hashlib.sha256(block_data.encode()).hexdigest()

        # Store encrypted vote
        ENCRYPTED_VOTES[vote_id] = {
            "vote_id": vote_id,
            "election_id": election_id,
            "ciphertext": ciphertext,
            "client_hash": client_hash,
            "ledger_index": ledger_index,
            "ts": time.time(),
            "block_hash": block_hash
        }

        # Store ledger block
        block_key = (election_id, ledger_index)
        LEDGER_BLOCKS[block_key] = {
            "index": ledger_index,
            "election_id": election_id,
            "vote_hash": vote_hash,
            "prev_hash": prev_hash,
            "hash": block_hash,
            "ts": time.time()
        }

        # Mark OVT as spent
        ovt_token["status"] = "spent"

        # Mark voter as having voted
        if ves_key in VOTER_ELECTION_STATUS:
            VOTER_ELECTION_STATUS[ves_key]["voted_flag"] = True

        # Return an RSA-PSS signed receipt
        receipt_payload = {
            "vote_id": vote_id,
            "election_id": election_id,
            "ledger_index": ledger_index,
            "block_hash": block_hash
        }
        h = SHA256.new(json.dumps(receipt_payload, sort_keys=True, separators=(",", ":")).encode())
        sig = pss.new(RSA_SK).sign(h)
        receipt_sig = base64.b64encode(sig).decode()

        print(f"DEBUG: Vote stored and signed receipt ready. vote_id={vote_id}, ledger_index={ledger_index}")

        return jsonify({
            "ledger_index": ledger_index,
            "block_hash": block_hash,
            "receipt": {
                **receipt_payload,
                "sig": receipt_sig
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": {
                "code": "VOTE_FAILED",
                "message": str(e)
            }
        }), 500

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