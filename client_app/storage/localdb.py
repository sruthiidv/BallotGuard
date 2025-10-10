import sqlite3, time

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

def store_receipt(vote_id: str, election_id: str, idx: int, bhash: str, sig_b64: str | None, db_path="client_local.db"):
    con = connect(db_path)
    con.execute("""INSERT OR REPLACE INTO receipts(vote_id,election_id,ledger_index,block_hash,receipt_sig,created_ms)
                   VALUES(?,?,?,?,?,?)""",
                (vote_id, election_id, idx, bhash, sig_b64 or "", int(time.time()*1000)))
    con.commit()
    con.close()
