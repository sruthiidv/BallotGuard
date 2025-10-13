from flask import Flask, request, jsonify
import uuid
import time
from server_backend.crypto import sha_utils, paillier_server
from server_backend.blockchain import blockchain as blockchain_mod
from datetime import datetime
import sys
import os
import sqlite3

# Ensure server/ is in the Python path for imports
sys.path.append(os.path.dirname(__file__))

# Requirements:
# pip install face_recognition numpy pycryptodome
# Plus dlib for face_recognition (use prebuilt wheels on Windows)

import json, base64
import numpy as np
import face_recognition

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from server_config import RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM, PAILLIER_N, PAILLIER_P, PAILLIER_Q

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

#########################
# MVP Architecture Data Structures
# VOTERS now in SQLite
VOTER_ELECTION_STATUS = None  # Deprecated: now using SQLite for voter election status
OVT_TOKENS = None  # Deprecated: now using SQLite for OVT tokens
ENCRYPTED_VOTES = None  # Deprecated: now using SQLite for encrypted votes
LEDGER_BLOCKS = None    # Deprecated: now using SQLite for ledger blocks

# Counters for ledger indices per election (now in DB)
def get_next_ledger_index(election_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT MAX(ledger_index) FROM ledger_blocks WHERE election_id=?", (election_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0] is not None:
        return row[0] + 1
    else:
        return 0

# SQLite DB setup for voters
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'server_voters.db')
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_voters_table():
    conn = get_db()
    c = conn.cursor()
    # Voters table
    c.execute('''CREATE TABLE IF NOT EXISTS voters (
        voter_id TEXT PRIMARY KEY,
        face_encoding TEXT,
        status TEXT,
        created_at REAL
    )''')
    # OVT tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS ovt_tokens (
        ovt_uuid TEXT PRIMARY KEY,
        election_id TEXT,
        voter_id TEXT,
        status TEXT,
        expires_at REAL,
        issued_ts REAL
    )''')
    # Encrypted votes table (add voter_id column)
    c.execute('''CREATE TABLE IF NOT EXISTS encrypted_votes (
        vote_id TEXT PRIMARY KEY,
        election_id TEXT,
        voter_id TEXT,
        ciphertext TEXT,
        client_hash TEXT,
        ledger_index INTEGER,
        ts REAL,
        block_hash TEXT
    )''')
    # Ledger blocks table
    c.execute('''CREATE TABLE IF NOT EXISTS ledger_blocks (
        election_id TEXT,
        ledger_index INTEGER,
        vote_hash TEXT,
        prev_hash TEXT,
        hash TEXT,
        ts REAL,
        PRIMARY KEY (election_id, ledger_index)
    )''')
    # Voter election status table
    c.execute('''CREATE TABLE IF NOT EXISTS voter_election_status (
        election_id TEXT,
        voter_id TEXT,
        status TEXT,
        voted_flag INTEGER,
        last_auth_ts REAL,
        PRIMARY KEY (election_id, voter_id)
    )''')
    conn.commit()
    conn.close()
init_voters_table()

# MVP Architecture Endpoints

@app.route('/elections', methods=['GET'])
def get_elections():
    """Get list of all elections"""
    return jsonify(ELECTIONS)

# Voters endpoints (Admin)
@app.route('/voters/enroll', methods=['POST'])
def enroll_voter():
    """Enroll a new voter - now using SQLite for persistence"""
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

        # Store in SQLite
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO voters (voter_id, face_encoding, status, created_at) VALUES (?, ?, ?, ?)",
                  (voter_id, json.dumps(enc.tolist()), "pending", time.time()))
        conn.commit()
        conn.close()

        # Auto-approve after 3 seconds (for demo)
        def auto_approve_sqlite():
            time.sleep(3)
            conn2 = get_db()
            c2 = conn2.cursor()
            c2.execute("UPDATE voters SET status=? WHERE voter_id=?", ("active", voter_id))
            # Make voter eligible for all open elections (in DB)
            for election in ELECTIONS:
                if election["status"] == "open":
                    c2.execute("INSERT OR REPLACE INTO voter_election_status (election_id, voter_id, status, voted_flag, last_auth_ts) VALUES (?, ?, ?, ?, ?)",
                        (election["election_id"], voter_id, "active", 0, None))
            conn2.commit()
            conn2.close()

        import threading
        threading.Thread(target=auto_approve_sqlite, daemon=True).start()

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
    """Approve a voter - now using SQLite for persistence"""
    # Check if voter exists in DB
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM voters WHERE voter_id=?", (voter_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Voter not found"
            }
        }), 404
    # Update status to active
    c.execute("UPDATE voters SET status=? WHERE voter_id=?", ("active", voter_id))
    conn.commit()
    conn.close()
    # Make eligible for all open elections (in DB)
    conn2 = get_db()
    c2 = conn2.cursor()
    for election in ELECTIONS:
        if election["status"] == "open":
            c2.execute("INSERT OR REPLACE INTO voter_election_status (election_id, voter_id, status, voted_flag, last_auth_ts) VALUES (?, ?, ?, ?, ?)",
                (election["election_id"], voter_id, "active", 0, None))
    conn2.commit()
    conn2.close()
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

        # Fetch voter from SQLite
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM voters WHERE voter_id=?", (voter_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            print(f"DEBUG: Face verify failed - unknown voter. voter_id={voter_id}")
            return jsonify({"error":{"code":"NOT_FOUND","message":"Voter not found"}}), 404
        if row["status"] != "active":
            return jsonify({"error":{"code":"VOTER_INACTIVE","message":"Voter not approved"}}), 403

        # Check eligibility and voted_flag from DB
        conn2 = get_db()
        c2 = conn2.cursor()
        c2.execute("SELECT status, voted_flag FROM voter_election_status WHERE election_id=? AND voter_id=?", (election_id, voter_id))
        ves_row = c2.fetchone()
        conn2.close()
        if not ves_row or ves_row["status"] != "active":
            return jsonify({"error":{"code":"NOT_ELIGIBLE","message":"Not eligible for this election"}}), 403
        if ves_row["voted_flag"]:
            return jsonify({"error":{"code":"ALREADY_VOTED","message":"Already voted in this election"}}), 409

        try:
            stored = np.asarray(json.loads(row["face_encoding"]), dtype=float)
            probe = np.asarray(probe_encoding, dtype=float)
            matches = face_recognition.compare_faces([stored], probe, tolerance=0.5)
            distance = float(face_recognition.face_distance([stored], probe)[0])
            passed = bool(matches[0])
            confidence = max(0.0, 1.0 - distance)  # heuristic
        except Exception as e:
            return jsonify({"error":{"code":"FACE_COMPARE_FAIL","message":str(e)}}), 500

        # Update last_auth_ts in DB
        conn2 = get_db()
        c2 = conn2.cursor()
        c2.execute("UPDATE voter_election_status SET last_auth_ts=? WHERE election_id=? AND voter_id=?", (time.time(), election_id, voter_id))
        conn2.commit()
        conn2.close()

        print(f"DEBUG: Face verify {'PASS' if passed else 'FAIL'}. voter_id={voter_id}, election_id={election_id}, conf={confidence:.3f}")
        return jsonify({"pass": passed, "confidence": confidence, "voter_id": voter_id})
    except Exception as e:
        return jsonify({"error":{"code":"AUTH_FAIL","message":str(e)}}), 500

@app.route('/ovt/issue', methods=['POST'])
def issue_ovt():
    """Issue OVT token - now using SQLite for persistence"""
    try:
        data = request.json
        voter_id = data.get("voter_id")
        election_id = data.get("election_id")

        # Validate voter and election eligibility
        # Check eligibility and voted_flag from DB
        conn2 = get_db()
        c2 = conn2.cursor()
        c2.execute("SELECT status, voted_flag FROM voter_election_status WHERE election_id=? AND voter_id=?", (election_id, voter_id))
        ves_row = c2.fetchone()
        conn2.close()
        if not ves_row or ves_row["status"] != "active":
            return jsonify({
                "error": {
                    "code": "NOT_ELIGIBLE",
                    "message": "Not eligible for this election"
                }
            }), 403
        if ves_row["voted_flag"]:
            return jsonify({
                "error": {
                    "code": "ALREADY_VOTED", 
                    "message": "Already voted in this election"
                }
            }), 409

        # Revoke any existing unspent OVTs for this voter/election in DB
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE ovt_tokens SET status=? WHERE voter_id=? AND election_id=? AND status=?", ("expired", voter_id, election_id, "issued"))

        # Generate new OVT
        ovt_uuid = str(uuid.uuid4())
        now = time.time()
        expires_at = now + 300  # 5 minutes TTL

        ovt = {
            "ovt_uuid": ovt_uuid,
            "election_id": election_id,
            "voter_id": voter_id,
            "not_before": now,
            "expires_at": expires_at
        }

        # Store OVT in DB
        c.execute("INSERT INTO ovt_tokens (ovt_uuid, election_id, voter_id, status, expires_at, issued_ts) VALUES (?, ?, ?, ?, ?, ?)",
                  (ovt_uuid, election_id, voter_id, "issued", expires_at, now))
        conn.commit()
        conn.close()

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
    """Cast a vote - now using SQLite for persistence"""
    try:
        data = request.json
        vote_id = data.get("vote_id")
        election_id = data.get("election_id")
        candidate_id = data.get("candidate_id")
        ciphertext = data.get("ciphertext", "mock_encrypted_vote")
        client_hash = data.get("client_hash")
        ovt = data.get("ovt", {})
        ovt_uuid = ovt.get("ovt_uuid") if ovt else None

        # Validate OVT (from DB)
        if not ovt_uuid:
            return jsonify({"error": {"code": "OVT_NOT_FOUND","message": "Invalid or missing OVT"}}), 400
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM ovt_tokens WHERE ovt_uuid=?", (ovt_uuid,))
        ovt_token = c.fetchone()
        if not ovt_token:
            conn.close()
            return jsonify({"error": {"code": "OVT_NOT_FOUND","message": "Invalid or missing OVT"}}), 400
        if ovt_token["status"] != "issued":
            conn.close()
            return jsonify({"error": {"code": "OVT_SPENT","message": "OVT already used"}}), 409
        if ovt_token["expires_at"] < time.time():
            conn.close()
            return jsonify({"error": {"code": "OVT_EXPIRED", "message": "OVT expired"}}), 403
        if ovt_token["election_id"] != election_id:
            conn.close()
            return jsonify({"error": {"code": "OVT_ELECTION_MISMATCH","message": "OVT not issued for this election"}}), 403
        voter_id = ovt_token["voter_id"]

        # Check if already voted
        # Check eligibility and voted_flag from DB
        conn2 = get_db()
        c2 = conn2.cursor()
        c2.execute("SELECT status, voted_flag FROM voter_election_status WHERE election_id=? AND voter_id=?", (election_id, voter_id))
        ves_row = c2.fetchone()
        if not ves_row or ves_row["status"] != "active":
            conn2.close()
            conn.close()
            return jsonify({"error": {"code": "NOT_ELIGIBLE","message": "Not eligible for this election"}}), 403
        if ves_row["voted_flag"]:
            conn2.close()
            conn.close()
            return jsonify({"error": {"code": "ALREADY_VOTED","message": "Already voted in this election"}}), 409

        # Check for duplicate vote_id (idempotency)
        c.execute("SELECT * FROM encrypted_votes WHERE vote_id=?", (vote_id,))
        existing_vote = c.fetchone()
        if existing_vote:
            conn.close()
            return jsonify({
                "ledger_index": existing_vote["ledger_index"],
                "block_hash": existing_vote["block_hash"],
                "ack": "stored"
            })

        # Get election salt for vote_hash
        election_salt = "default_salt"
        for election in ELECTIONS:
            if election["election_id"] == election_id:
                election_salt = election.get("election_salt", "default_salt")
                break

        # Compute vote_hash using real SHA-256 util
        vote_hash = sha_utils.compute_sha256_hex(f"{ciphertext}{election_salt}")

        # Get next ledger index from DB
        ledger_index = get_next_ledger_index(election_id)
        if ledger_index == 0:
            prev_hash = "GENESIS"
        else:
            c.execute("SELECT hash FROM ledger_blocks WHERE election_id=? AND ledger_index=?", (election_id, ledger_index-1))
            prev_row = c.fetchone()
            prev_hash = prev_row["hash"] if prev_row else "GENESIS"

        # Use real blockchain Block class for block creation
        block_header = {
            "index": ledger_index,
            "timestamp": time.time(),
            "vote_hash": vote_hash,
            "previous_hash": prev_hash
        }
        # Compute block hash using Block class
        block_obj = blockchain_mod.Block(
            index=ledger_index,
            timestamp=block_header["timestamp"],
            vote_hash=vote_hash,
            previous_hash=prev_hash
        )
        block_hash = block_obj.hash

        # Store encrypted vote in DB (include voter_id, 8 columns)
        c.execute("INSERT INTO encrypted_votes (vote_id, election_id, voter_id, ciphertext, client_hash, ledger_index, ts, block_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (vote_id, election_id, voter_id, ciphertext, client_hash, ledger_index, block_header["timestamp"], block_hash))

        # Store ledger block in DB (with real block hash)
        c.execute("INSERT INTO ledger_blocks (election_id, ledger_index, vote_hash, prev_hash, hash, ts) VALUES (?, ?, ?, ?, ?, ?)",
                  (election_id, ledger_index, vote_hash, prev_hash, block_hash, block_header["timestamp"]))

        # Mark OVT as spent
        c.execute("UPDATE ovt_tokens SET status=? WHERE ovt_uuid=?", ("spent", ovt_uuid))

        conn.commit()
        conn.close()

        # Mark voter as having voted (in DB)
        c2.execute("UPDATE voter_election_status SET voted_flag=1 WHERE election_id=? AND voter_id=?", (election_id, voter_id))
        conn2.commit()
        conn2.close()

        # Return an RSA-PSS signed receipt (restore original logic)
        receipt_payload = {
            "vote_id": vote_id,
            "election_id": election_id,
            "ledger_index": ledger_index,
            "block_hash": block_hash
        }
        # Compute signature as before
        from Crypto.Hash import SHA256
        from Crypto.Signature import pss
        import base64
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
    # Count voters from SQLite
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voters")
    voters_count = c.fetchone()[0]
    conn.close()
    # Count votes and OVT tokens from DB
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM encrypted_votes")
    votes_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ovt_tokens")
    ovt_tokens_count = c.fetchone()[0]
    conn.close()
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "elections_count": len(ELECTIONS),
        "voters_count": voters_count,
        "votes_count": votes_count,
        "ovt_tokens_count": ovt_tokens_count
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