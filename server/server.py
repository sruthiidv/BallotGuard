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

from flask import Flask, request, jsonify, render_template
import uuid
import time
from server_backend.crypto import sha_utils, paillier_server
from server_backend.blockchain import blockchain as blockchain_mod

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

# Import cryptographic libraries (REQUIRED - no fallback)
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from server_config import RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM, PAILLIER_N, PAILLIER_P, PAILLIER_Q

app = Flask(__name__)

# Rate Limiting Setup
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri="memory://",
    )
    print("[SECURITY] ✓ Rate limiting enabled")
except ImportError:
    print("[SECURITY] ⚠ Flask-Limiter not installed. Rate limiting disabled.")
    print("            Install with: pip install Flask-Limiter")
    limiter = None

# Face authentication lockout tracking
# Format: {voter_id: [(timestamp, success_bool), ...]}
AUTH_ATTEMPTS = {}
AUTH_LOCKOUT_DURATION = 900  # 15 minutes in seconds
MAX_AUTH_FAILURES = 3  # Lock after 3 failed attempts within 60 seconds

# Party Symbols Dictionary - Indian Political Parties
PARTY_SYMBOLS = {
    "BJP": "🌸",          # Lotus
    "INC": "✋",          # Hand
    "AAP": "🧹",          # Broom
    "CPI": "🌾",          # Ears of Corn
    "TMC": "🌿",          # Grass flower and leaves
    "Independent": "⭐",   # Star
    "": "🗳️"              # Default ballot box
}

# Initialize RSA keys for signing
RSA_SK = RSA.import_key(RECEIPT_RSA_PRIV_PEM)
RSA_PUB_PEM = RECEIPT_RSA_PUB_PEM  # returned to clients for verification

def sign_bytes_with_crypto(data_bytes):
    """Sign bytes using RSA-PSS with SHA-256"""
    h = SHA256.new(data_bytes)
    sig = pss.new(RSA_SK).sign(h)
    sig_b64 = base64.b64encode(sig).decode()
    print(f"[CRYPTO] ✓ Signed {len(data_bytes)} bytes -> signature {sig_b64[:32]}...")
    return sig_b64

def sign_block_header(block_header):
    """Sign a blockchain block header using RSA-PSS"""
    header_bytes = json.dumps(block_header, sort_keys=True, separators=(",", ":")).encode()
    print(f"[CRYPTO] Signing block #{block_header.get('index')} header...")
    return sign_bytes_with_crypto(header_bytes)

def verify_block_signature(block_header, signature_b64):
    """Verify a blockchain block signature using RSA-PSS"""
    try:
        header_bytes = json.dumps(block_header, sort_keys=True, separators=(",", ":")).encode()
        h = SHA256.new(header_bytes)
        sig = base64.b64decode(signature_b64)
        pss.new(RSA_SK).verify(h, sig)
        print(f"[CRYPTO] ✓ Block #{block_header.get('index')} signature VALID")
        return True
    except Exception as e:
        print(f"[CRYPTO] ✗ Block #{block_header.get('index')} signature INVALID: {e}")
        return False

# Face encoding encryption setup
# Generate encryption key from server secret (deterministic for same server)
FACE_ENCRYPTION_KEY = PBKDF2("BallotGuard-FaceData-Secret-2025", b"biometric-salt", dkLen=32, count=100000)

def encrypt_face_encoding(face_encoding_json):
    """Encrypt face encoding JSON string using AES-256-GCM"""
    try:
        nonce = get_random_bytes(16)
        cipher = AES.new(FACE_ENCRYPTION_KEY, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(face_encoding_json.encode())
        # Store as: base64(nonce || tag || ciphertext)
        encrypted = base64.b64encode(nonce + tag + ciphertext).decode()
        print(f"[CRYPTO] ✓ Face encoding encrypted ({len(face_encoding_json)} bytes)")
        return encrypted
    except Exception as e:
        print(f"[CRYPTO] ✗ Face encoding encryption failed: {e}")
        return None

def decrypt_face_encoding(encrypted_b64):
    """Decrypt face encoding from AES-256-GCM encrypted format"""
    try:
        data = base64.b64decode(encrypted_b64)
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        cipher = AES.new(FACE_ENCRYPTION_KEY, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()
    except Exception as e:
        print(f"[CRYPTO] ✗ Face encoding decryption failed: {e}")
        return None

def log_audit_event(event_type, user_id, election_id=None, details=None, success=True):
    """Log security-relevant events to audit trail"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO audit_log 
                     (event_type, user_id, election_id, details, success, ip_address, timestamp) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (event_type, user_id, election_id, details, 1 if success else 0, 
                   request.remote_addr if request else "system", time.time()))
        conn.commit()
        conn.close()
        print(f"[AUDIT] {event_type}: user={user_id}, election={election_id}, success={success}")
    except Exception as e:
        print(f"[AUDIT] ✗ Failed to log audit event: {e}")

@app.route('/public-key', methods=['GET'])
def get_public_key():
    return jsonify({"rsa_pub_pem": RSA_PUB_PEM})

@app.route('/party-symbols', methods=['GET'])
def get_party_symbols():
    """Get available party symbols for election creation"""
    return jsonify(PARTY_SYMBOLS)

# Initial elections data
INITIAL_ELECTIONS = [
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
    """Find election by ID with lenient matching.

    Accepts either 'election_id' or 'id' keys, tolerates extra display text
    (like 'EL-2025-01: Name'), and matches case-insensitively.
    Returns the election dict or None.
    """
    if not election_id:
        return None

    # Normalize the election ID
    key = _normalize_eid(str(election_id))
    
    # Try to load from DB first
    try:
        return load_election_from_db(key)
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
        name TEXT,
        face_encoding TEXT,
        status TEXT,
        created_at REAL
    )''')
    
    # Tampered blocks backup table for demonstration
    c.execute('''CREATE TABLE IF NOT EXISTS tampered_blocks_backup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        election_id TEXT,
        ledger_index INTEGER,
        original_vote_hash TEXT,
        original_hash TEXT,
        tampered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        signature TEXT,
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
    
    # Audit log table for security events
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        user_id TEXT,
        election_id TEXT,
        details TEXT,
        success INTEGER DEFAULT 1,
        ip_address TEXT,
        timestamp REAL NOT NULL
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_type)')
    
    conn.commit()
    conn.close()
init_voters_table()


def ensure_voters_name_column():
    """Add name column to voters table if it doesn't exist"""
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA table_info(voters)")
    cols = [row[1] for row in c.fetchall()]
    if 'name' not in cols:
        try:
            c.execute("ALTER TABLE voters ADD COLUMN name TEXT")
            conn.commit()
        except Exception:
            pass
    conn.close()

ensure_voters_name_column()


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


def ensure_ledger_blocks_signature_column():
    """Add signature column to ledger_blocks table if it doesn't exist"""
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA table_info(ledger_blocks)")
    cols = [row[1] for row in c.fetchall()]
    if 'signature' not in cols:
        try:
            c.execute("ALTER TABLE ledger_blocks ADD COLUMN signature TEXT")
            conn.commit()
            print("Added signature column to ledger_blocks table")
        except Exception as e:
            print(f"Error adding signature column: {e}")
    conn.close()

ensure_ledger_blocks_signature_column()


def init_elections_table():
    """Create elections table and seed with initial election data if empty."""
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
    # Seed from initial election data if table is empty
    c.execute("SELECT COUNT(*) FROM elections")
    if c.fetchone()[0] == 0:
        for e in INITIAL_ELECTIONS:
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
    """Get list of all elections
    
    Query parameter: 
    - include_closed=true to include closed elections (for admin)
    - Default: exclude closed elections (for voters)
    """
    try:
        include_closed = request.args.get('include_closed', 'false').lower() == 'true'
        
        # Get all elections from the database
        db_list = load_all_elections_from_db()
        
        # Filter out closed elections unless explicitly requested
        if not include_closed:
            db_list = [e for e in db_list if e.get('status') != 'closed']
        
        return jsonify(db_list)
    except Exception as e:
        return jsonify({"error": {"code": "LOAD_FAILED", "message": str(e)}}), 500


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
            party = c.get('party') or 'Independent'
            # Auto-assign symbol based on party if not provided
            symbol = c.get('symbol') or PARTY_SYMBOLS.get(party, PARTY_SYMBOLS.get('', '🗳️'))
            normalized.append({
                'candidate_id': c.get('candidate_id') or f"C{idx}",
                'name': c.get('name') or c.get('candidate_name') or f"Candidate {idx}",
                'party': party,
                'symbol': symbol
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

        # Save election to database
        save_election_to_db(election)

        # Note: Voters must be manually approved for this election by admin
        # No automatic voter enrollment

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
@limiter.limit("10 per hour") if limiter else lambda f: f
def enroll_voter():
    """Enroll a new voter - now using SQLite for persistence"""
    try:
        data = request.json
        # Generate unique voter ID
        voter_id = f"VOTER-{str(uuid.uuid4())[:8].upper()}"

        # Get voter name (optional but recommended)
        voter_name = data.get("name", "").strip() or "Anonymous"

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

        # Store in SQLite with encrypted face encoding
        face_encoding_json = json.dumps(enc.tolist())
        encrypted_encoding = encrypt_face_encoding(face_encoding_json)
        
        if not encrypted_encoding:
            return jsonify({"error":{"code":"ENCRYPTION_FAILED","message":"Failed to encrypt biometric data"}}), 500
        
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO voters (voter_id, name, face_encoding, status, created_at) VALUES (?, ?, ?, ?, ?)",
                  (voter_id, voter_name, encrypted_encoding, "pending", time.time()))
        conn.commit()
        conn.close()
        
        # Audit log
        log_audit_event("VOTER_ENROLLED", voter_id, None, f"name={voter_name}", True)

        # NOTE: Do NOT auto-approve voters here. Voters are created with status 'pending'
        # and must be approved by an administrator via the admin API (/voters/<id>/approve).
        # This preserves real-world workflow and prevents accidental auto-activation.

        return jsonify({
            "voter_id": voter_id,
            "name": voter_name,
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
    """Approve a voter for a specific election - per-election approval"""
    try:
        data = request.json or {}
        election_id = data.get('election_id')
        
        if not election_id:
            return jsonify({
                "error": {
                    "code": "MISSING_ELECTION",
                    "message": "election_id is required for approval"
                }
            }), 400
        
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
        
        # Update voter's global status to active (if not already)
        if row['status'] != 'active':
            c.execute("UPDATE voters SET status=? WHERE voter_id=?", ("active", voter_id))
            conn.commit()
        
        # Verify election exists
        c.execute("SELECT * FROM elections WHERE election_id=?", (election_id,))
        election = c.fetchone()
        if not election:
            conn.close()
            return jsonify({
                "error": {
                    "code": "ELECTION_NOT_FOUND",
                    "message": f"Election {election_id} not found"
                }
            }), 404
        
        # Add voter to this specific election's voter_election_status
        c.execute("SELECT * FROM voter_election_status WHERE election_id=? AND voter_id=?",
                  (election_id, voter_id))
        existing = c.fetchone()
        
        if not existing:
            # Insert new entry for this election
            c.execute("INSERT INTO voter_election_status (election_id, voter_id, status, voted_flag, last_auth_ts) VALUES (?, ?, ?, ?, ?)",
                (election_id, voter_id, "active", 0, None))
        else:
            # Update existing entry to active
            c.execute("UPDATE voter_election_status SET status=? WHERE election_id=? AND voter_id=?",
                ("active", election_id, voter_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "active",
            "election_id": election_id,
            "voter_id": voter_id,
            "message": f"Voter {voter_id} approved for election {election_id}"
        })
        
    except Exception as e:
        return jsonify({
            "error": {
                "code": "APPROVAL_FAILED",
                "message": str(e)
            }
        }), 500


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
            c.execute("SELECT voter_id, name, face_encoding, status, created_at FROM voters WHERE status=? ORDER BY created_at DESC", (status,))
        else:
            c.execute("SELECT voter_id, name, face_encoding, status, created_at FROM voters ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        out = []
        for r in rows:
            out.append({
                'voter_id': r['voter_id'],
                'name': r['name'] if r['name'] else 'Anonymous',
                'status': r['status'],
                'created_at': r['created_at']
            })
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": {"code": "FAILED", "message": str(e)}}), 500

@app.route('/voters/<voter_id>/election-status/<election_id>', methods=['GET'])
def get_voter_election_status(voter_id, election_id):
    """Check if voter is approved for a specific election"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Check voter exists
        c.execute("SELECT status FROM voters WHERE voter_id=?", (voter_id,))
        voter = c.fetchone()
        if not voter:
            conn.close()
            return jsonify({"approved": False, "reason": "voter_not_found"})
        
        # Check election-specific status
        c.execute("SELECT status, voted_flag FROM voter_election_status WHERE election_id=? AND voter_id=?",
                  (election_id, voter_id))
        election_status = c.fetchone()
        conn.close()
        
        if not election_status:
            return jsonify({"approved": False, "reason": "not_approved_for_election"})
        
        if election_status['status'] != 'active':
            return jsonify({"approved": False, "reason": "blocked_or_inactive"})
        
        if election_status['voted_flag']:
            return jsonify({"approved": True, "already_voted": True})
        
        return jsonify({"approved": True, "already_voted": False})
        
    except Exception as e:
        return jsonify({"error": {"code": "CHECK_FAILED", "message": str(e)}}), 500

# Auth & OVT endpoints (Booth)
@app.route('/auth/face/verify', methods=['POST'])
@limiter.limit("20 per minute") if limiter else lambda f: f
def verify_face():
    """Face verification - real encoding match using face_recognition with lockout protection"""
    try:
        data = request.json
        voter_id = data.get("voter_id")
        election_id = data.get("election_id")
        probe_encoding = data.get("face_encoding") or data.get("face_template")

        if not voter_id or not probe_encoding:
            return jsonify({"error":{"code":"NO_DATA","message":"Missing voter_id or face_encoding"}}), 400

        # Check for authentication lockout
        current_time = time.time()
        if voter_id in AUTH_ATTEMPTS:
            # Clean old attempts (older than 60 seconds)
            AUTH_ATTEMPTS[voter_id] = [(t, s) for t, s in AUTH_ATTEMPTS[voter_id] if current_time - t < 60]
            
            # Count recent failures
            recent_failures = [t for t, s in AUTH_ATTEMPTS[voter_id] if not s]
            if len(recent_failures) >= MAX_AUTH_FAILURES:
                # Check if still locked out
                oldest_failure = min(recent_failures)
                if current_time - oldest_failure < AUTH_LOCKOUT_DURATION:
                    remaining = int(AUTH_LOCKOUT_DURATION - (current_time - oldest_failure))
                    print(f"[AUTH] ⚠ LOCKOUT: Voter {voter_id} locked for {remaining}s (failed attempts: {len(recent_failures)})")
                    return jsonify({
                        "error": {
                            "code": "ACCOUNT_LOCKED",
                            "message": f"Too many failed attempts. Account locked for {remaining} seconds. Contact administrator."
                        }
                    }), 429
                else:
                    # Lockout expired, clear attempts
                    AUTH_ATTEMPTS[voter_id] = []

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
            # Decrypt face encoding
            decrypted_encoding = decrypt_face_encoding(row["face_encoding"])
            if not decrypted_encoding:
                log_audit_event("FACE_AUTH_FAILED", voter_id, election_id, "Decryption failed", False)
                return jsonify({"error":{"code":"DECRYPTION_FAILED","message":"Failed to decrypt biometric data"}}), 500
            
            stored = np.asarray(json.loads(decrypted_encoding), dtype=float)
            probe = np.asarray(probe_encoding, dtype=float)
            matches = face_recognition.compare_faces([stored], probe, tolerance=0.5)
            distance = float(face_recognition.face_distance([stored], probe)[0])
            passed = bool(matches[0])
            confidence = max(0.0, 1.0 - distance)  # heuristic
        except Exception as e:
            log_audit_event("FACE_AUTH_ERROR", voter_id, election_id, str(e), False)
            return jsonify({"error":{"code":"FACE_COMPARE_FAIL","message":str(e)}}), 500

        # Track authentication attempt
        if voter_id not in AUTH_ATTEMPTS:
            AUTH_ATTEMPTS[voter_id] = []
        AUTH_ATTEMPTS[voter_id].append((current_time, passed))
        print(f"[AUTH] Face verification: voter_id={voter_id}, result={'PASS' if passed else 'FAIL'}, confidence={confidence:.3f}, total_attempts={len(AUTH_ATTEMPTS[voter_id])}")
        
        # Audit log
        log_audit_event("FACE_AUTH", voter_id, election_id, f"confidence={confidence:.3f}", passed)

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
@limiter.limit("30 per hour") if limiter else lambda f: f
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
        print(f"[OVT] Issuing OVT for voter_id={voter_id}, election_id={election_id}, ovt_uuid={ovt_uuid}")
        ovt_bytes = json.dumps(ovt, sort_keys=True, separators=(",", ":")).encode()
        server_sig = sign_bytes_with_crypto(ovt_bytes)
        print(f"[OVT] ✓ OVT signed and ready for client")
        
        # Audit log
        log_audit_event("OVT_ISSUED", voter_id, election_id, f"ovt_uuid={ovt_uuid}", True)

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
@limiter.limit("10 per hour") if limiter else lambda f: f
def cast_vote():
    """Cast a vote - now using SQLite for persistence"""
    try:
        data = request.json
        vote_id = data.get("vote_id")
        election_id = data.get("election_id")
        candidate_id = data.get("candidate_id")
        
        # Handle encrypted_vote object from client
        encrypted_vote = data.get("encrypted_vote", {})
        if isinstance(encrypted_vote, dict):
            ciphertext = encrypted_vote.get("ciphertext")
            # Ensure ciphertext is a string representation of the number
            if ciphertext:
                ciphertext = str(ciphertext)
        else:
            ciphertext = data.get("ciphertext", "mock_encrypted_vote")
        
        # Validate we have a proper ciphertext
        if not ciphertext or ciphertext == "mock_encrypted_vote":
            return jsonify({"error": {"code": "INVALID_VOTE", "message": "Invalid encrypted vote"}}), 400
            
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
        # Get election metadata from DB
        try:
            db_election = load_election_from_db(election_id)
            if db_election and db_election.get('election_salt'):
                election_salt = db_election.get('election_salt')
        except Exception as e:
            print(f"Warning: Could not load election salt from DB: {e}")
            pass

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

        # Sign the block header using RSA-PSS (critical security feature)
        print(f"[VOTE] Signing blockchain block for vote_id={vote_id}, ledger_index={ledger_index}")
        block_signature = sign_block_header(block_header)
        
        # Update ledger block with signature
        c.execute("UPDATE ledger_blocks SET signature=? WHERE election_id=? AND ledger_index=?",
                  (block_signature, election_id, ledger_index))
        print(f"[VOTE] ✓ Block signature stored in database")

        # Mark OVT as spent
        c.execute("UPDATE ovt_tokens SET status=? WHERE ovt_uuid=?", ("spent", ovt_uuid))

        conn.commit()
        conn.close()

        # Mark voter as having voted (in DB)
        c2.execute("UPDATE voter_election_status SET voted_flag=1 WHERE election_id=? AND voter_id=?", (election_id, voter_id))
        conn2.commit()
        conn2.close()
        
        # Audit log
        log_audit_event("VOTE_CAST", voter_id, election_id, f"vote_id={vote_id},candidate_id={candidate_id},ledger_index={ledger_index}", True)

        # Return an RSA-PSS signed receipt (restore original logic)
        receipt_payload = {
            "vote_id": vote_id,
            "election_id": election_id,
            "ledger_index": ledger_index,
            "block_hash": block_hash
        }
        # Compute receipt signature
        print(f"[RECEIPT] Generating signed receipt for vote_id={vote_id}")
        payload_bytes = json.dumps(receipt_payload, sort_keys=True, separators=(",", ":")).encode()
        receipt_sig = sign_bytes_with_crypto(payload_bytes)
        print(f"[RECEIPT] ✓ Receipt signed and ready for client")

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

@app.route('/admin/verify', methods=['GET'])
def admin_verify_page():
    """Admin interface for blockchain verification"""
    return render_template('admin_verify.html')

@app.route('/admin/simulate-tampering/<election_id>', methods=['POST'])
def simulate_tampering(election_id):
    """Simulate tampering with the blockchain for demonstration"""
    try:
        data = request.get_json(silent=True) or {}
        action = data.get('action', 'tamper')
        
        conn = get_db()
        c = conn.cursor()
        
        # Create backup table if it doesn't exist
        c.execute("""CREATE TABLE IF NOT EXISTS tampered_blocks_backup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id TEXT,
            ledger_index INTEGER,
            original_vote_hash TEXT,
            original_hash TEXT,
            tampered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        if action == 'untamper':
            # Find the most recent tampered block
            c.execute("""
                SELECT * FROM tampered_blocks_backup 
                WHERE election_id = ? 
                ORDER BY tampered_at DESC LIMIT 1""", (election_id,))
            backup = c.fetchone()
            
            if not backup:
                conn.close()
                return jsonify({
                    "message": "No tampered blocks found to restore",
                    "details": "The blockchain has not been tampered with or has already been restored"
                })
            
            # Restore the original block data
            c.execute("""
                UPDATE ledger_blocks 
                SET vote_hash = ?, hash = ?
                WHERE election_id = ? AND ledger_index = ?""", 
                (backup['original_vote_hash'], backup['original_hash'],
                 election_id, backup['ledger_index']))
            
            # Remove the backup record
            c.execute("DELETE FROM tampered_blocks_backup WHERE id = ?", (backup['id'],))
            conn.commit()
            conn.close()
            
            return jsonify({
                "message": "Successfully restored the blockchain",
                "details": f"Block #{backup['ledger_index']} has been restored to its original state"
            })
        
        # For tampering action
        # Get a random non-genesis block
        c.execute("""
            SELECT ledger_index, vote_hash, hash 
            FROM ledger_blocks 
            WHERE election_id = ? AND ledger_index > 0 
            ORDER BY RANDOM() LIMIT 1""", (election_id,))
        block = c.fetchone()
        
        if not block:
            conn.close()
            return jsonify({
                "message": "No blocks available for tampering",
                "details": "The blockchain needs at least one non-genesis block"
            })

        # Backup original block data before tampering
        c.execute("""
            INSERT INTO tampered_blocks_backup 
            (election_id, ledger_index, original_vote_hash, original_hash)
            VALUES (?, ?, ?, ?)""", 
            (election_id, block['ledger_index'], block['vote_hash'], block['hash']))

        # Simulate tampering by modifying the vote hash
        tampered_hash = "TAMPERED_" + sha_utils.compute_sha256_hex(str(time.time()))
        c.execute("""
            UPDATE ledger_blocks 
            SET vote_hash = ? 
            WHERE election_id = ? AND ledger_index = ?""",
            (tampered_hash, election_id, block['ledger_index']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": f"Simulated tampering at Block #{block['ledger_index']}",
            "details": "Modified the vote hash to break the blockchain's integrity. Use 'Verify' to see the impact and 'Undo Tampering' to restore."
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({"error": "OPERATION_FAILED", "message": str(e)}), 500
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Verify election exists and is in appropriate state
        c.execute("SELECT * FROM elections WHERE election_id = ?", (election_id,))
        election = c.fetchone()
        if not election:
            return jsonify({"error": "NOT_FOUND", "message": "Election not found"}), 404
        
        # Get a random block (not genesis)
        c.execute("""
            SELECT ledger_index, vote_hash, hash
            FROM ledger_blocks 
            WHERE election_id = ? AND ledger_index > 0 
            ORDER BY RANDOM() 
            LIMIT 1""", (election_id,))
        block = c.fetchone()
        
        if not block:
            return jsonify({
                "message": "No blocks available for tampering demonstration"
            })

        # Simulate tampering by modifying the vote hash
        tampered_hash = "TAMPERED_" + block["vote_hash"][:20]
        c.execute("""
            UPDATE ledger_blocks 
            SET vote_hash=? 
            WHERE election_id=? AND ledger_index=?""",
            (tampered_hash, election_id, block["ledger_index"]))
        
        conn.commit()
        conn.close()

        return jsonify({
            "message": f"Simulated tampering at block {block['ledger_index']}. Verify to see the effect!",
            "tampered_block": block["ledger_index"]
        })

    except Exception as e:
        return jsonify({
            "error": f"Error simulating tampering: {str(e)}"
        }), 500

@app.route('/blockchain/verify/<election_id>', methods=['GET'])
def verify_blockchain(election_id):
    """Comprehensive blockchain verification with visual feedback"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get election details
        c.execute("SELECT * FROM elections WHERE election_id = ?", (election_id,))
        election = c.fetchone()
        if not election:
            return jsonify({
                "error": "NOT_FOUND",
                "message": "Election not found"
            }), 404

        # Get all blocks and their details (including signatures)
        c.execute("""
            SELECT lb.ledger_index, lb.vote_hash, lb.prev_hash, lb.hash, lb.ts, lb.signature,
                   COUNT(ev.vote_id) as votes_in_block
            FROM ledger_blocks lb
            LEFT JOIN encrypted_votes ev ON 
                ev.election_id = lb.election_id AND 
                ev.ledger_index = lb.ledger_index
            WHERE lb.election_id = ?
            GROUP BY lb.ledger_index, lb.vote_hash, lb.prev_hash, lb.hash, lb.ts, lb.signature
            ORDER BY lb.ledger_index""", (election_id,))
        rows = c.fetchall()
        block_rows = [dict(row) for row in rows]
        
        if not block_rows:
            return jsonify({
                "status": "empty",
                "message": "No blocks found in blockchain",
                "total_blocks": 0,
                "total_votes": 0,
                "blocks": []
            })

        # Get total votes
        c.execute("SELECT COUNT(*) as count FROM encrypted_votes WHERE election_id = ?", (election_id,))
        total_votes = c.fetchone()["count"]

        # Verify blockchain integrity (hash chain + signatures)
        blocks = []
        prev_hash = "GENESIS"
        is_valid = True
        invalid_block = None
        signature_failures = []

        for row in block_rows:
            # Create block object for validation
            block_obj = blockchain_mod.Block(
                index=row["ledger_index"],
                timestamp=row["ts"],
                vote_hash=row["vote_hash"],
                previous_hash=row["prev_hash"]
            )

            # Check hash continuity
            hash_chain_valid = (row["prev_hash"] == prev_hash)
            if not hash_chain_valid:
                is_valid = False
                if invalid_block is None:
                    invalid_block = row["ledger_index"]

            # Check block hash validity
            hash_valid = (row["hash"] == block_obj.hash)
            if not hash_valid:
                is_valid = False
                if invalid_block is None:
                    invalid_block = row["ledger_index"]

            # CRITICAL SECURITY: Verify block signature
            signature_valid = False
            if row["signature"]:
                try:
                    block_header = {
                        "index": row["ledger_index"],
                        "timestamp": row["ts"],
                        "vote_hash": row["vote_hash"],
                        "previous_hash": row["prev_hash"]
                    }
                    signature_valid = verify_block_signature(block_header, row["signature"])
                except Exception as e:
                    print(f"WARNING: Block {row['ledger_index']} signature verification failed: {e}")
                    signature_failures.append({
                        "block": row["ledger_index"],
                        "error": str(e)
                    })
            else:
                print(f"WARNING: Block {row['ledger_index']} has no signature (legacy block)")

            # Add block to response
            blocks.append({
                "index": row["ledger_index"],
                "hash": row["hash"],
                "timestamp": row["ts"],
                "votes_in_block": row["votes_in_block"],
                "is_valid": hash_chain_valid and hash_valid,
                "signature_valid": signature_valid,
                "has_signature": bool(row["signature"])
            })

            prev_hash = row["hash"]

        # Prepare response
        response = {
            "status": "valid" if is_valid else "tampered",
            "message": "Blockchain verified successfully" if is_valid else f"Blockchain tampering detected at block {invalid_block}",
            "total_blocks": len(blocks),
            "total_votes": total_votes,
            "blocks": blocks,
            "signature_failures": signature_failures,
            "election": {
                "id": election["election_id"],
                "name": election["name"],
                "status": election["status"]
            }
        }

        conn.close()
        return jsonify(response)
        
        if not blocks:
            return jsonify({
                "message": "No votes found in blockchain",
                "status": "empty"
            })

        # Check if blockchain is intact
        is_valid = True
        tampered_block = None
        prev_hash = "GENESIS"
        
        for block in blocks:
            # Recalculate this block's hash
            block_obj = blockchain_mod.Block(
                index=block["ledger_index"],
                timestamp=block["ts"],
                vote_hash=block["vote_hash"],
                previous_hash=block["prev_hash"]
            )
            
            # Two checks:
            # 1. Does this block point to previous block correctly?
            # 2. Has this block's content been modified?
            if block["prev_hash"] != prev_hash or block["hash"] != block_obj.hash:
                is_valid = False
                tampered_block = block["ledger_index"]
                break
                
            prev_hash = block["hash"]

        # Get total votes for context
        c.execute("SELECT COUNT(*) FROM encrypted_votes WHERE election_id=?", (election_id,))
        total_votes = c.fetchone()[0]
        
        conn.close()

        # Prepare detailed block information
        block_details = []
        prev_hash = "GENESIS"
        for block in blocks:
            # Check this block's validity
            block_obj = blockchain_mod.Block(
                index=block["ledger_index"],
                timestamp=block["ts"],
                vote_hash=block["vote_hash"],
                previous_hash=block["prev_hash"]
            )
            
            is_block_valid = (block["prev_hash"] == prev_hash and 
                            block["hash"] == block_obj.hash)
            
            block_details.append({
                "index": block["ledger_index"],
                "hash": block["hash"],
                "vote_hash": block["vote_hash"],
                "prev_hash": block["prev_hash"],
                "timestamp": block["ts"],
                "is_valid": is_block_valid
            })
            
            prev_hash = block["hash"]

        if is_valid:
            return jsonify({
                "status": "valid",
                "message": "✅ Blockchain is intact - no tampering detected",
                "total_blocks": len(blocks),
                "total_votes": total_votes,
                "last_vote_time": blocks[-1]["ts"],
                "blocks": block_details
            })
        else:
            return jsonify({
                "status": "tampered",
                "message": f"❌ Tampering detected at block {tampered_block}!",
                "tampered_block": tampered_block,
                "total_blocks": len(blocks),
                "total_votes": total_votes,
                "blocks": block_details
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error checking blockchain: {str(e)}"
        }), 500

@app.route('/elections/<election_id>/progress', methods=['GET'])
def election_progress(election_id):
    """Get real-time election progress and verification stats"""
    try:
        conn = get_db()
        c = conn.cursor()

        # Get election details
        election = find_election(election_id)
        if not election:
            return jsonify({"error": "Election not found"}), 404

        # Get voting progress stats
        c.execute("""
            SELECT 
                COUNT(DISTINCT voter_id) as total_voters,
                SUM(CASE WHEN voted_flag = 1 THEN 1 ELSE 0 END) as votes_cast
            FROM voter_election_status 
            WHERE election_id = ? AND status = 'active'
        """, (election_id,))
        voter_stats = c.fetchone()

        # Get blockchain stats
        c.execute("""
            SELECT COUNT(*) as block_count, MAX(ts) as last_block_time
            FROM ledger_blocks 
            WHERE election_id = ?
        """, (election_id,))
        blockchain_stats = c.fetchone()

        # Calculate turnout
        total_voters = voter_stats["total_voters"] or 0
        votes_cast = voter_stats["votes_cast"] or 0
        turnout = (votes_cast / total_voters * 100) if total_voters > 0 else 0

        # Get voting activity timeline (last 6 hours)
        six_hours_ago = time.time() - (6 * 3600)
        c.execute("""
            SELECT strftime('%H:%M', datetime(ts, 'unixepoch', 'localtime')) as hour,
                   COUNT(*) as votes
            FROM encrypted_votes 
            WHERE election_id = ? AND ts > ?
            GROUP BY hour
            ORDER BY hour
        """, (election_id, six_hours_ago))
        activity = c.fetchall()

        conn.close()

        return jsonify({
            "election_id": election_id,
            "name": election["name"],
            "status": election["status"],
            "progress": {
                "eligible_voters": total_voters,
                "votes_cast": votes_cast,
                "turnout_percentage": round(turnout, 2),
                "blockchain_blocks": blockchain_stats["block_count"],
                "last_vote_time": blockchain_stats["last_block_time"]
            },
            "voting_timeline": [dict(row) for row in activity],
            "verification": {
                "blockchain_intact": verify_blockchain(election_id).json["status"] == "valid",
                "total_blocks_verified": blockchain_stats["block_count"]
            }
        })

    except Exception as e:
        return jsonify({
            "error": f"Error getting election progress: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Count voters from SQLite
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voters")
    voters_count = c.fetchone()[0]
    # Count votes and OVT tokens from DB
    c.execute("SELECT COUNT(*) FROM encrypted_votes")
    votes_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ovt_tokens")
    ovt_tokens_count = c.fetchone()[0]
    # Count elections
    c.execute("SELECT COUNT(*) FROM elections")
    elections_count = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "elections_count": elections_count,
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


from server_backend.crypto import paillier_server
from phe import paillier

@app.route('/elections/<election_id>/results', methods=['GET'])
def get_election_results(election_id):
    """Tally votes for an election using homomorphic encryption."""
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

    # Get encrypted votes from database
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT candidate_id, ciphertext FROM encrypted_votes WHERE election_id=?", (found.get('election_id'),))
    rows = c.fetchall()
    conn.close()

    # Initialize Paillier cryptosystem
    try:
        public_key = paillier.PaillierPublicKey(PAILLIER_N)
        private_key = paillier.PaillierPrivateKey(public_key, PAILLIER_P, PAILLIER_Q)
    except Exception as e:
        return jsonify({"error": {"code": "CRYPTO_ERROR", "message": f"Error initializing cryptosystem: {str(e)}"}}), 500

    # Group encrypted votes by candidate
    candidate_votes = {}
    for row in rows:
        cid = row[0]
        cipher_str = row[1]
        if cid not in candidate_votes:
            candidate_votes[cid] = []
        try:
            # Deserialize encrypted vote - convert string to integer
            if cipher_str and cipher_str != "mock_encrypted_vote":
                cipher_int = int(cipher_str)
                enc_vote = paillier.EncryptedNumber(public_key, cipher_int)
                candidate_votes[cid].append(enc_vote)
                print(f"✅ Successfully loaded vote for candidate {cid}")
            else:
                print(f"⚠️ Skipping mock/invalid vote for candidate {cid}")
        except ValueError as e:
            print(f"❌ ValueError deserializing vote for candidate {cid}: {e}, ciphertext: {cipher_str[:50]}")
            continue
        except Exception as e:
            print(f"❌ Error deserializing vote for candidate {cid}: {e}")
            continue

    # Calculate encrypted sums and decrypt
    results_list = []
    total_votes = 0
    
    print(f"\n🔢 Tallying votes for election {found.get('election_id')}")
    print(f"📊 Candidates to tally: {[c.get('name') for c in candidates]}")
    print(f"📦 Encrypted votes by candidate: {[(cid, len(votes)) for cid, votes in candidate_votes.items()]}")

    for c_idx, cand in enumerate(candidates):
        cid = cand.get('candidate_id') or f"C{c_idx+1}"
        encrypted_votes = candidate_votes.get(cid, [])
        
        print(f"\n  Candidate: {cand.get('name')} (ID: {cid})")
        print(f"  Encrypted votes found: {len(encrypted_votes)}")
        
        if encrypted_votes:
            # Homomorphically sum encrypted votes
            sum_votes = encrypted_votes[0]
            for vote in encrypted_votes[1:]:
                sum_votes += vote
            
            # Decrypt sum
            try:
                vote_count = private_key.decrypt(sum_votes)
                print(f"  ✅ Decrypted vote count: {vote_count}")
            except Exception as e:
                print(f"  ❌ Could not decrypt sum for candidate {cid}: {e}")
                vote_count = 0
        else:
            vote_count = 0
            print(f"  ⚠️ No votes found")
            
        total_votes += vote_count

        # Calculate percentage
        pct = (vote_count / total_votes * 100) if total_votes else 0.0
        results_list.append({
            'candidate_id': cid,
            'name': cand.get('name'),
            'party': cand.get('party', ''),  # Include party for symbol display
            'votes': vote_count,
            'percentage': pct
        })

    # Get eligible voters count
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voter_election_status WHERE election_id=? AND status='active'", 
             (found.get('election_id'),))
    eligible_voters = c.fetchone()[0]
    conn.close()

    turnout = (total_votes / eligible_voters * 100) if eligible_voters else 0.0

    # Add any write-in candidates that weren't in original candidate list
    for cid in candidate_votes.keys():
        if not any(r['candidate_id'] == cid for r in results_list):
            encrypted_votes = candidate_votes[cid]
            if encrypted_votes:
                sum_votes = encrypted_votes[0]
                for vote in encrypted_votes[1:]:
                    sum_votes += vote
                try:
                    vote_count = private_key.decrypt(sum_votes)
                except Exception:
                    vote_count = 0
            else:
                vote_count = 0
                
            pct = (vote_count / total_votes * 100) if total_votes else 0.0
            results_list.append({
                'candidate_id': cid,
                'name': cand_map.get(cid, f"Write-in {cid}"),
                'party': '',  # Write-ins have no party
                'votes': vote_count,
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