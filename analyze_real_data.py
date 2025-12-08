"""
Analyze REAL performance from your actual database
This gives you TRUE production values!
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "database/server_voters.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 80)
print("REAL SYSTEM PERFORMANCE ANALYSIS")
print("=" * 80)

# 1. Authentication attempts timing
print("\n📊 AUTHENTICATION PERFORMANCE (from audit_log)")
c.execute("""
    SELECT event_type, COUNT(*) as count
    FROM audit_log 
    WHERE event_type IN ('FACE_AUTH', 'OVT_ISSUED', 'VOTE_CAST')
    GROUP BY event_type
""")
for row in c.fetchall():
    print(f"  {row['event_type']}: {row['count']} events")

# 2. Vote submission timing
print("\n📊 VOTE SUBMISSION TIMING")
c.execute("""
    SELECT 
        COUNT(*) as total_votes,
        MIN(ts) as first_vote,
        MAX(ts) as last_vote
    FROM encrypted_votes
""")
row = c.fetchone()
if row and row['total_votes'] > 0:
    print(f"  Total votes cast: {row['total_votes']}")
    first = datetime.fromtimestamp(row['first_vote']).strftime('%Y-%m-%d %H:%M:%S') if row['first_vote'] else 'N/A'
    last = datetime.fromtimestamp(row['last_vote']).strftime('%Y-%m-%d %H:%M:%S') if row['last_vote'] else 'N/A'
    print(f"  First vote: {first}")
    print(f"  Last vote: {last}")
    if row['total_votes'] > 1:
        duration = row['last_vote'] - row['first_vote']
        print(f"  Duration: {duration:.2f} seconds")
        avg_interval = duration / (row['total_votes'] - 1) if row['total_votes'] > 1 else 0
        print(f"  Avg interval between votes: {avg_interval:.2f} seconds")
else:
    print("  No votes in database yet")

# 3. OVT issuance stats
print("\n📊 OVT TOKEN STATS")
c.execute("SELECT COUNT(*) as total, COUNT(DISTINCT voter_id) as unique_voters FROM ovt_tokens")
row = c.fetchone()
print(f"  Total OVTs issued: {row['total']}")
print(f"  Unique voters: {row['unique_voters']}")

# 4. Blockchain stats
print("\n📊 BLOCKCHAIN STATS (from ledger_blocks)")
c.execute("""
    SELECT election_id, COUNT(*) as block_count, MAX(ledger_index) as max_index
    FROM ledger_blocks
    GROUP BY election_id
""")
blocks = c.fetchall()
if blocks:
    for row in blocks:
        print(f"  Election {row['election_id']}: {row['block_count']} blocks, max index: {row['max_index']}")
else:
    print("  No blockchain blocks yet")

# 5. Audit log summary
print("\n📊 SECURITY EVENTS")
c.execute("SELECT event_type, COUNT(*) as count FROM audit_log GROUP BY event_type ORDER BY count DESC")
for row in c.fetchall():
    print(f"  {row['event_type']}: {row['count']} events")

conn.close()

print("\n" + "=" * 80)
print("✅ This is REAL data from your actual system!")
print("💡 Cast some test votes to get more timing data")
print("=" * 80)
