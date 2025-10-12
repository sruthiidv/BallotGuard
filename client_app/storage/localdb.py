import sqlite3
import time
import hashlib
import json

DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS receipts(
  vote_id TEXT PRIMARY KEY,
  election_id TEXT NOT NULL,
  ledger_index INTEGER NOT NULL,
  block_hash TEXT NOT NULL,
  receipt_sig TEXT,
  created_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ovts(
  token TEXT PRIMARY KEY,
  election_id TEXT NOT NULL,
  used INTEGER DEFAULT 0,
  created_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS votes(
  vote_id TEXT PRIMARY KEY,
  election_id TEXT NOT NULL,
  encrypted_vote TEXT NOT NULL,
  ovt_token TEXT NOT NULL,
  created_ms INTEGER NOT NULL
);
"""

def connect(db_path="client_local.db"):
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.execute("PRAGMA busy_timeout=5000;")
    return con

def init(db_path="client_local.db"):
    con = connect(db_path)
    for stmt in filter(None, DDL.split(';')):
        con.execute(stmt)
    con.commit()
    con.close()


# --- Ledger Receipts ---
def store_receipt(vote_id: str, election_id: str, idx: int, bhash: str, sig_b64: str | None, db_path="client_local.db"):
    con = connect(db_path)
    con.execute("""INSERT OR REPLACE INTO receipts(vote_id,election_id,ledger_index,block_hash,receipt_sig,created_ms)
                   VALUES(?,?,?,?,?,?)""",
                (vote_id, election_id, idx, bhash, sig_b64 or "", int(time.time()*1000)))
    con.commit()
    con.close()

def fetch_last_receipt(election_id: str, db_path="client_local.db"):
    """Returns last ledger index and block hash for an election."""
    con = connect(db_path)
    cur = con.execute(
        "SELECT ledger_index, block_hash FROM receipts WHERE election_id=? ORDER BY ledger_index DESC LIMIT 1",
        (election_id,)
    )
    row = cur.fetchone()
    con.close()
    if row:
        return row[0], row[1]
    else:
        return 0, "0"  # Genesis block


# --- OVTs ---
def store_ovt(token: str, election_id: str, db_path="client_local.db"):
    con = connect(db_path)
    con.execute(
        "INSERT OR REPLACE INTO ovts(token,election_id,used,created_ms) VALUES(?,?,?,?)",
        (token, election_id, 0, int(time.time()*1000))
    )
    con.commit()
    con.close()

def mark_ovt_used(token: str, db_path="client_local.db"):
    con = connect(db_path)
    con.execute("UPDATE ovts SET used=1 WHERE token=?", (token,))
    con.commit()
    con.close()

def is_ovt_used(token: str, db_path="client_local.db") -> bool:
    con = connect(db_path)
    cur = con.execute("SELECT used FROM ovts WHERE token=?", (token,))
    row = cur.fetchone()
    con.close()
    return row[0] == 1 if row else True  # treat missing token as used/invalid


# --- Encrypted Votes ---
def store_vote(vote_id: str, election_id: str, encrypted_vote: str, ovt_token: str, db_path="client_local.db"):
    con = connect(db_path)
    con.execute(
        "INSERT OR REPLACE INTO votes(vote_id,election_id,encrypted_vote,ovt_token,created_ms) VALUES(?,?,?,?,?)",
        (vote_id, election_id, encrypted_vote, ovt_token, int(time.time()*1000))
    )
    con.commit()
    con.close()

def fetch_encrypted_votes(election_id: str, db_path="client_local.db"):
    con = connect(db_path)
    cur = con.execute("SELECT encrypted_vote FROM votes WHERE election_id=?", (election_id,))
    votes = [row[0] for row in cur.fetchall()]
    con.close()
    return votes
