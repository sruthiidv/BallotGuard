import sqlite3
import json

conn = sqlite3.connect('database/server_voters.db')
c = conn.cursor()

# Get election details
c.execute("SELECT election_id, name, candidates FROM elections WHERE election_id LIKE 'EL-2025%'")
elections = c.fetchall()

print("=== ELECTIONS ===")
for e in elections:
    print(f"\nElection ID: {e[0]}")
    print(f"Name: {e[1]}")
    candidates = json.loads(e[2])
    print(f"Candidates:")
    for i, cand in enumerate(candidates):
        print(f"  {i}. {cand.get('name')} - ID: {cand.get('candidate_id', 'N/A')} - Party: {cand.get('party', 'N/A')}")

# Get vote counts
print("\n=== VOTES IN DATABASE ===")
c.execute("SELECT election_id, candidate_id, ciphertext FROM encrypted_votes ORDER BY election_id, candidate_id")
votes = c.fetchall()

for v in votes:
    print(f"Election: {v[0]} | Candidate ID: {v[1]} | Ciphertext: {v[2][:50]}...")

# Group by election and candidate
print("\n=== VOTE COUNTS BY CANDIDATE ===")
c.execute("SELECT election_id, candidate_id, COUNT(*) FROM encrypted_votes GROUP BY election_id, candidate_id")
counts = c.fetchall()

for r in counts:
    print(f"Election: {r[0]} | Candidate ID: {r[1]} | Count: {r[2]}")

conn.close()
