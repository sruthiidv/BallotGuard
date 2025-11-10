"""
Election database operations. This replaces the in-memory ELECTIONS list with proper DB storage.
"""

import sqlite3
import uuid
import time
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'server_voters.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_elections_table():
    """Create elections table if it doesn't exist"""
    conn = get_db()
    c = conn.cursor()
    
    # Elections table
    c.execute('''CREATE TABLE IF NOT EXISTS elections (
        election_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT,
        candidates TEXT,  -- JSON array
        election_salt TEXT,
        created_at REAL,
        updated_at REAL
    )''')
    
    # Election audit log
    c.execute('''CREATE TABLE IF NOT EXISTS election_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        election_id TEXT,
        action TEXT,
        details TEXT,  -- JSON
        ts REAL,
        FOREIGN KEY (election_id) REFERENCES elections(election_id)
    )''')
    
    conn.commit()
    conn.close()

def create_election(name: str, start_date: str, end_date: str) -> dict:
    """Create a new election"""
    conn = get_db()
    c = conn.cursor()
    
    election_id = f"EL-{str(uuid.uuid4())[:8].upper()}"
    now = time.time()
    
    try:
        c.execute("""
            INSERT INTO elections (
                election_id, name, status, start_date, end_date,
                candidates, election_salt, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            election_id, name, "draft", start_date, end_date,
            "[]",  # Empty candidates array
            os.urandom(8).hex(),  # Random salt
            now, now
        ))
        
        # Log creation
        c.execute("""
            INSERT INTO election_audit_log (election_id, action, details, ts)
            VALUES (?, ?, ?, ?)
        """, (
            election_id,
            "election_created",
            json.dumps({
                "name": name,
                "start_date": start_date,
                "end_date": end_date
            }),
            now
        ))
        
        conn.commit()
        
        # Return created election
        c.execute("SELECT * FROM elections WHERE election_id = ?", (election_id,))
        election = dict(c.fetchone())
        election["candidates"] = json.loads(election["candidates"])
        
        return election
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_elections() -> list:
    """Get all elections"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM elections ORDER BY created_at DESC")
    elections = []
    for row in c.fetchall():
        election = dict(row)
        election["candidates"] = json.loads(election["candidates"])
        elections.append(election)
    
    conn.close()
    return elections

def get_election(election_id: str) -> dict:
    """Get a single election by ID"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM elections WHERE election_id = ?", (election_id,))
    row = c.fetchone()
    if not row:
        return None
        
    election = dict(row)
    election["candidates"] = json.loads(election["candidates"])
    
    conn.close()
    return election

def update_election_status(election_id: str, new_status: str) -> dict:
    """Update election status"""
    valid_statuses = {"draft", "open", "closed", "paused", "archived"}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Update status
        c.execute("""
            UPDATE elections 
            SET status = ?, updated_at = ?
            WHERE election_id = ?
        """, (new_status, time.time(), election_id))
        
        # Log status change
        c.execute("""
            INSERT INTO election_audit_log (election_id, action, details, ts)
            VALUES (?, ?, ?, ?)
        """, (
            election_id,
            "status_changed",
            json.dumps({"new_status": new_status}),
            time.time()
        ))
        
        conn.commit()
        
        # Return updated election
        return get_election(election_id)
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def add_candidate(election_id: str, name: str, party: str) -> dict:
    """Add a candidate to an election"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get current candidates
        c.execute("SELECT candidates FROM elections WHERE election_id = ?", (election_id,))
        row = c.fetchone()
        if not row:
            raise ValueError("Election not found")
            
        candidates = json.loads(row["candidates"])
        
        # Generate candidate ID
        candidate_id = f"C{len(candidates) + 1}"
        
        # Add new candidate
        candidates.append({
            "candidate_id": candidate_id,
            "name": name,
            "party": party
        })
        
        # Update candidates and timestamp
        c.execute("""
            UPDATE elections 
            SET candidates = ?, updated_at = ?
            WHERE election_id = ?
        """, (json.dumps(candidates), time.time(), election_id))
        
        # Log candidate addition
        c.execute("""
            INSERT INTO election_audit_log (election_id, action, details, ts)
            VALUES (?, ?, ?, ?)
        """, (
            election_id,
            "candidate_added",
            json.dumps({
                "candidate_id": candidate_id,
                "name": name,
                "party": party
            }),
            time.time()
        ))
        
        conn.commit()
        
        # Return updated election
        return get_election(election_id)
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Initialize tables
init_elections_table()