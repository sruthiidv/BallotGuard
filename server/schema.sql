-- Schema for tampered blocks backup
CREATE TABLE IF NOT EXISTS tampered_blocks_backup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    election_id TEXT,
    ledger_index INTEGER,
    original_vote_hash TEXT,
    original_hash TEXT,
    tampered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);