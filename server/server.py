import sys
import os

# Ensure project root is on sys.path so sibling packages like `server_backend`
# (which live at the repository root) can be imported when running this module
# from the `server/` directory. This must run before importing server_backend.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Ensure server/ is in the Python path for imports
SERVER_DIR = os.path.dirname(__file__)
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from flask import Flask, request, jsonify
import uuid
import time
from server_backend.crypto import sha_utils, paillier_server
from server_backend.blockchain import blockchain as blockchain_mod
from datetime import datetime
import sqlite3

# Requirements:
# pip install face_recognition numpy pycryptodome
# Plus dlib for face_recognition (use prebuilt wheels on Windows)

import json, base64
import numpy as np
try:
    import face_recognition  # optional heavy dependency
    FACE_RECOG_AVAILABLE = True
except Exception:
    # Provide a lightweight numpy-based fallback for demos when face_recognition
    # (and its heavy dependency dlib) is not available on the machine.
    FACE_RECOG_AVAILABLE = False

    class _FallbackFaceRecog:
        @staticmethod
        def compare_faces(known_encodings, probe_encoding, tolerance=0.6):
            """Return list of booleans whether distance <= tolerance"""
            try:
                probe = np.asarray(probe_encoding, dtype=float)
                results = []
                for k in known_encodings:
                    k_arr = np.asarray(k, dtype=float)
                    dist = np.linalg.norm(k_arr - probe)
                    results.append(dist <= tolerance)
                return results
            except Exception:
                return [False for _ in known_encodings]

        @staticmethod
        def face_distance(known_encodings, probe_encoding):
            try:
                probe = np.asarray(probe_encoding, dtype=float)
                dists = []
                for k in known_encodings:
                    k_arr = np.asarray(k, dtype=float)
                    dists.append(float(np.linalg.norm(k_arr - probe)))
                return np.array(dists)
            except Exception:
                return np.array([1e6 for _ in known_encodings])

    face_recognition = _FallbackFaceRecog()

try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pss
    from Crypto.Hash import SHA256
    from server_config import RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM, PAILLIER_N, PAILLIER_P, PAILLIER_Q
    CRYPTO_AVAILABLE = True
except Exception:
    # Fallback: pycryptodome not available. Provide a non-cryptographic fallback
    # signing function so the demo server can run. This is INSECURE and only for
    # local demos when installing pycryptodome is not possible.
    import hashlib
    from server_config import RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM, PAILLIER_N, PAILLIER_P, PAILLIER_Q
    CRYPTO_AVAILABLE = False

app = Flask(__name__)

if CRYPTO_AVAILABLE:
    RSA_SK = RSA.import_key(RECEIPT_RSA_PRIV_PEM)
    RSA_PUB_PEM = RECEIPT_RSA_PUB_PEM  # returned to clients for verification
    def sign_bytes_with_crypto(data_bytes):
        h = SHA256.new(data_bytes)
        sig = pss.new(RSA_SK).sign(h)
        return base64.b64encode(sig).decode()
else:
    RSA_SK = None
    RSA_PUB_PEM = RECEIPT_RSA_PUB_PEM
    def sign_bytes_with_crypto(data_bytes):
        # Insecure fallback: return base64(sha256(data)) as a placeholder signature
        digest = hashlib.sha256(data_bytes).digest()
        return base64.b64encode(digest).decode()

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


def _normalize_eid(eid: str) -> str:
    if not eid:
        return eid
    # Strip whitespace and any trailing display text like "EL-123: Name"
    eid = eid.strip()
    if ':' in eid:
        eid = eid.split(':', 1)[0].strip()
    return eid


def find_election(election_id):
    """Find election object in ELECTIONS with lenient matching.

    Accepts either 'election_id' or 'id' keys, tolerates extra display text
    (like 'EL-2025-01: Name'), and matches case-insensitively.
    Returns the election dict or None.
    """
    if not election_id:
        return None
    key = _normalize_eid(str(election_id))
    lk = key.lower()
    for e in ELECTIONS:
        # Check canonical keys
        for candidate_key in ("election_id", "id", "id_str"):
            val = e.get(candidate_key)
            if val and str(val).strip().lower() == lk:
                return e
        # Also compare against any stringified id-like values
        if str(e.get('election_id', '')).strip().lower() == lk:
            return e
        if str(e.get('id', '')).strip().lower() == lk:
            return e
    # Try DB fallback (in case server restarted and ELECTIONS not in-memory)
    try:
        db_eid = _normalize_eid(key)
        db_found = load_election_from_db(db_eid)
        if db_found:
            # Cache in-memory for faster future lookups
            ELECTIONS.append(db_found)
            return db_found
    except Exception:
        pass
    return None

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
        candidate_id TEXT,
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


def ensure_encrypted_votes_candidate_column():
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA table_info(encrypted_votes)")
    cols = [row[1] for row in c.fetchall()]
    if 'candidate_id' not in cols:
        try:
            c.execute("ALTER TABLE encrypted_votes ADD COLUMN candidate_id TEXT")
            conn.commit()
        except Exception:
            pass
    conn.close()

ensure_encrypted_votes_candidate_column()


def init_elections_table():
    """Create elections table and seed with in-memory ELECTIONS if empty."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS elections (
        election_id TEXT PRIMARY KEY,
        name TEXT,
        status TEXT,
        start_date TEXT,
        end_date TEXT,
        description TEXT,
        candidates TEXT,
        election_salt TEXT,
        eligible_voters INTEGER DEFAULT 0
    )''')
    # Seed from in-memory ELECTIONS if table is empty
    c.execute("SELECT COUNT(*) FROM elections")
    if c.fetchone()[0] == 0:
        for e in ELECTIONS:
            try:
                c.execute("INSERT OR REPLACE INTO elections (election_id, name, status, start_date, end_date, description, candidates, election_salt, eligible_voters) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (e.get('election_id'), e.get('name'), e.get('status', 'draft'), e.get('start_date', ''), e.get('end_date', ''), e.get('description', ''), json.dumps(e.get('candidates', [])), e.get('election_salt', ''), e.get('eligible_voters', 0)))
            except Exception:
                pass
        conn.commit()
    conn.close()


def save_election_to_db(election: dict):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO elections (election_id, name, status, start_date, end_date, description, candidates, election_salt, eligible_voters) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (election.get('election_id'), election.get('name'), election.get('status', 'draft'), election.get('start_date', ''), election.get('end_date', ''), election.get('description', ''), json.dumps(election.get('candidates', [])), election.get('election_salt', ''), election.get('eligible_voters', 0)))
    conn.commit()
    conn.close()


def load_all_elections_from_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT election_id, name, status, start_date, end_date, description, candidates, election_salt, eligible_voters FROM elections ORDER BY election_id")
    rows = c.fetchall()
    conn.close()
    out = []
    for r in rows:
        try:
            candidates = json.loads(r[6]) if r[6] else []
        except Exception:
            candidates = []
        out.append({
            'election_id': r[0],
            'id': r[0],
            'name': r[1],
            'status': r[2],
            'start_date': r[3],
            'end_date': r[4],
            'description': r[5],
            'candidates': candidates,
            'election_salt': r[7],
            'eligible_voters': r[8] or 0
        })
    return out


def load_election_from_db(election_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT election_id, name, status, start_date, end_date, description, candidates, election_salt, eligible_voters FROM elections WHERE election_id=?", (election_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return None
    try:
        candidates = json.loads(r[6]) if r[6] else []
    except Exception:
        candidates = []
    return {
        'election_id': r[0],
        'id': r[0],
        'name': r[1],
        'status': r[2],
        'start_date': r[3],
        'end_date': r[4],
        'description': r[5],
        'candidates': candidates,
        'election_salt': r[7],
        'eligible_voters': r[8] or 0
    }

init_elections_table()

# MVP Architecture Endpoints

@app.route('/elections', methods=['GET'])
def get_elections():
    """Get list of all elections"""
    try:
        # Prefer DB-backed elections so created elections persist
        db_list = load_all_elections_from_db()
        if db_list:
            return jsonify(db_list)
    except Exception:
        pass
    # Fallback to in-memory list
    return jsonify(ELECTIONS)


@app.route('/elections/<election_id>', methods=['GET'])
def get_election(election_id):
    """Get a single election by id"""
    found = find_election(election_id)
    if found:
        return jsonify(found)
    return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404


@app.route('/elections', methods=['POST'])
def create_election():
    """Create a new election and persist it in memory (and prepare DB eligibility for open elections)

    Expected JSON payload: {
        'name': str,
        'description': str,
        'start_date': 'YYYY-MM-DDT..',
        'end_date': 'YYYY-MM-DDT..',
        'candidates': [ { 'name': ..., 'party': ... }, ... ]
    }
    Returns: created election with election_id
    """
    try:
        data = request.json or {}
        name = data.get('name') or data.get('title') or data.get('name')
        if not name:
            return jsonify({"error": {"code": "NO_NAME", "message": "Election name required"}}), 400

        # Generate simple election id
        election_id = f"EL-{str(uuid.uuid4())[:8].upper()}"

        # Normalize candidates
        candidates = data.get('candidates') or []
        normalized = []
        for idx, c in enumerate(candidates, start=1):
            normalized.append({
                'candidate_id': c.get('candidate_id') or f"C{idx}",
                'name': c.get('name') or c.get('candidate_name') or f"Candidate {idx}",
                'party': c.get('party') or 'Independent'
            })

        election = {
            'election_id': election_id,
            'id': election_id,
            'name': name,
            'title': name,
            'status': data.get('status') or 'draft',
            'start_date': data.get('start_date', '')[:10],
            'end_date': data.get('end_date', '')[:10],
            'description': data.get('description', ''),
            'candidates': normalized,
            'election_salt': data.get('election_salt') or uuid.uuid4().hex[:8]
        }

        # Add to in-memory list and persist to DB
        ELECTIONS.append(election)
        try:
            save_election_to_db(election)
        except Exception:
            pass

        # If created as open, prepare voter_election_status entries for active voters
        if election['status'] == 'open':
            conn = get_db()
            c = conn.cursor()
            # All active voters should be eligible
            c.execute("SELECT voter_id FROM voters WHERE status=?", ("active",))
            rows = c.fetchall()
            for r in rows:
                c.execute("INSERT OR REPLACE INTO voter_election_status (election_id, voter_id, status, voted_flag, last_auth_ts) VALUES (?, ?, ?, ?, ?)",
                          (election_id, r['voter_id'], 'active', 0, None))
            conn.commit()
            conn.close()

        return jsonify(election), 201
    except Exception as e:
        return jsonify({"error": {"code": "CREATE_FAILED", "message": str(e)}}), 500


@app.route('/elections/<election_id>/<action>', methods=['POST'])
def election_action(election_id, action):
    """Perform actions on an election: open, close, archive, reset

    open -> set status to 'open' and make existing active voters eligible
    close -> set status to 'closed'
    archive -> set status to 'archived'
    reset -> remove votes and ledger blocks for the election and reset voter voted_flag
    """
    try:
        found = find_election(election_id)
        if not found:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

        action = action.lower()
        if action == 'open':
            found['status'] = 'open'
            # persist status change
            try:
                save_election_to_db(found)
            except Exception:
                pass
            # Add eligibility for existing active voters
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT voter_id FROM voters WHERE status=?", ("active",))
            rows = c.fetchall()
            for r in rows:
                c.execute("INSERT OR REPLACE INTO voter_election_status (election_id, voter_id, status, voted_flag, last_auth_ts) VALUES (?, ?, ?, ?, ?)",
                          (election_id, r['voter_id'], 'active', 0, None))
            conn.commit()
            conn.close()
        elif action == 'close' or action == 'end':
            found['status'] = 'closed'
            try:
                save_election_to_db(found)
            except Exception:
                pass
        elif action == 'archive':
            found['status'] = 'archived'
            try:
                save_election_to_db(found)
            except Exception:
                pass
        elif action == 'reset':
            # Remove encrypted votes and ledger blocks for this election
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM encrypted_votes WHERE election_id=?", (election_id,))
            c.execute("DELETE FROM ledger_blocks WHERE election_id=?", (election_id,))
            # Reset voted flags
            c.execute("UPDATE voter_election_status SET voted_flag=0 WHERE election_id=?", (election_id,))
            conn.commit()
            conn.close()
            found['status'] = 'draft'
            try:
                save_election_to_db(found)
            except Exception:
                pass
        else:
            return jsonify({"error": {"code": "BAD_ACTION", "message": f"Unknown action: {action}"}}), 400

        return jsonify({"status": "ok", "election_id": election_id, "action": action}), 200
    except Exception as e:
        return jsonify({"error": {"code": "ACTION_FAILED", "message": str(e)}}), 500

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

        # NOTE: Do NOT auto-approve voters here. Voters are created with status 'pending'
        # and must be approved by an administrator via the admin API (/voters/<id>/approve).
        # This preserves real-world workflow and prevents accidental auto-activation.

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


@app.route('/voters/<voter_id>/block', methods=['POST'])
def block_voter(voter_id):
    """Block a voter: set status to 'blocked' and prevent issuance/verification."""
    try:
        conn = get_db()
        c = conn.cursor()
        # Verify voter exists
        c.execute("SELECT * FROM voters WHERE voter_id=?", (voter_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Voter not found"}}), 404

        # Set voter status to blocked
        c.execute("UPDATE voters SET status=? WHERE voter_id=?", ("blocked", voter_id))

        # Update any voter_election_status rows for this voter to blocked
        c.execute("UPDATE voter_election_status SET status=? WHERE voter_id=?", ("blocked", voter_id))

        conn.commit()
        conn.close()
        return jsonify({"status": "blocked", "voter_id": voter_id})
    except Exception as e:
        return jsonify({"error": {"code": "BLOCK_FAILED", "message": str(e)}}), 500


@app.route('/voters', methods=['GET'])
def get_voters():
    """Return list of voters. Optional query param: ?status=pending|active|all"""
    try:
        status = request.args.get('status', '').lower()
        conn = get_db()
        c = conn.cursor()
        if status and status != 'all':
            c.execute("SELECT voter_id, face_encoding, status, created_at FROM voters WHERE status=? ORDER BY created_at DESC", (status,))
        else:
            c.execute("SELECT voter_id, face_encoding, status, created_at FROM voters ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        out = []
        for r in rows:
            out.append({
                'voter_id': r['voter_id'],
                'status': r['status'],
                'created_at': r['created_at']
            })
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": {"code": "FAILED", "message": str(e)}}), 500

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
        server_sig = sign_bytes_with_crypto(ovt_bytes)

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
        # Prefer DB-backed election metadata
        try:
            db_election = load_election_from_db(election_id)
            if db_election and db_election.get('election_salt'):
                election_salt = db_election.get('election_salt')
            else:
                for election in ELECTIONS:
                    if election.get("election_id") == election_id or election.get('id') == election_id:
                        election_salt = election.get("election_salt", "default_salt")
                        break
        except Exception:
            # Fallback to in-memory
            for election in ELECTIONS:
                if election.get("election_id") == election_id or election.get('id') == election_id:
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

        # Store encrypted vote in DB (include voter_id and candidate_id)
        c.execute("INSERT INTO encrypted_votes (vote_id, election_id, voter_id, candidate_id, ciphertext, client_hash, ledger_index, ts, block_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (vote_id, election_id, voter_id, candidate_id, ciphertext, client_hash, ledger_index, block_header["timestamp"], block_hash))

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
        # Compute signature (use crypto if available, otherwise demo fallback)
        payload_bytes = json.dumps(receipt_payload, sort_keys=True, separators=(",", ":")).encode()
        receipt_sig = sign_bytes_with_crypto(payload_bytes)

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


@app.route('/elections/<election_id>/proof', methods=['GET'])
def get_election_proof(election_id):
    """Return ledger blocks (proof) for an election"""
    # Verify election exists
    found = find_election(election_id)
    if not found:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT ledger_index, vote_hash, prev_hash, hash, ts FROM ledger_blocks WHERE election_id=? ORDER BY ledger_index", (election_id,))
    rows = c.fetchall()
    conn.close()
    blocks = []
    for r in rows:
        blocks.append({
            "ledger_index": r[0],
            "vote_hash": r[1],
            "prev_hash": r[2],
            "hash": r[3],
            "ts": r[4]
        })
    return jsonify({"election_id": election_id, "blocks": blocks})


@app.route('/elections/<election_id>/results', methods=['GET'])
def get_election_results(election_id):
    """Tally votes for an election and return results per candidate."""
    found = find_election(election_id)
    if not found:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Election not found"}}), 404

    # Load candidate list
    try:
        db_election = load_election_from_db(found.get('election_id')) or found
    except Exception:
        db_election = found

    candidates = db_election.get('candidates', [])
    # Build candidate map id -> name
    cand_map = {c.get('candidate_id') or c.get('id') or str(i): c.get('name') for i, c in enumerate(candidates)}

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT candidate_id, COUNT(*) as cnt FROM encrypted_votes WHERE election_id=? GROUP BY candidate_id", (found.get('election_id'),))
    rows = c.fetchall()
    conn.close()

    counts = {r[0]: r[1] for r in rows}
    total_votes = sum(counts.values())
    eligible_voters = db_election.get('eligible_voters', 0) or 0
    turnout = (total_votes / eligible_voters * 100) if eligible_voters else 0.0

    results_list = []
    # Ensure all defined candidates appear in results (zero if none)
    for c_idx, cand in enumerate(candidates):
        cid = cand.get('candidate_id') or f"C{c_idx+1}"
        votes = counts.get(cid, 0)
        pct = (votes / total_votes * 100) if total_votes else 0.0
        results_list.append({
            'candidate_id': cid,
            'name': cand.get('name'),
            'votes': votes,
            'percentage': pct
        })

    # Also include any candidate_ids that appeared in DB but not in candidate list
    for cid, votes in counts.items():
        if not any(r['candidate_id'] == cid for r in results_list):
            pct = (votes / total_votes * 100) if total_votes else 0.0
            results_list.append({
                'candidate_id': cid,
                'name': cand_map.get(cid, cid),
                'votes': votes,
                'percentage': pct
            })

    # Determine winner(s)
    winner = None
    if results_list:
        max_votes = max(r['votes'] for r in results_list)
        winners = [r for r in results_list if r['votes'] == max_votes]
        if len(winners) == 1:
            winner = winners[0]
        else:
            # Tie - return list
            winner = { 'tie': True, 'winners': winners }

    return jsonify({
        'election_id': found.get('election_id'),
        'total_votes': total_votes,
        'eligible_voters': eligible_voters,
        'turnout_percentage': turnout,
        'results': results_list,
        'winner': winner
    })

if __name__ == '__main__':
    print("🗳️  BallotGuard Dummy Server Starting...")
    print("📡 Server running on: http://127.0.0.1:8443")
    print("📋 Available endpoints:")
    print("   GET  /elections")
    print("   GET  /elections/<id>")
    print("   GET  /elections/<id>/proof")
    print("   POST /elections")
    print("   POST /elections/<id>/<action>")
    print("   POST /voters/enroll")
    print("   POST /voters/<id>/approve")
    print("   POST /auth/face/verify")
    print("   POST /ovt/issue")
    print("   POST /votes")
    print("   GET  /health")
    print("-" * 50)
    app.run(host='127.0.0.1', port=8443, debug=True)