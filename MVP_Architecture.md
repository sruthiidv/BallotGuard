## MVP Architecture

**Objective:** Build a local (single‑machine) MVP that delivers: (a) admin‑verified enrollment, (b) face‑verified voting, (c) unlinkable encrypted ballots, (d) tamper‑evident per‑election ledger, and (e) verifiable final tally. The same interfaces extend to a remote server later.

**Core guarantees:**

- **Authenticity:** Admin enrollment + face verification with liveness and lockout.
- **Confidentiality:** Paillier encryption; only **totals** are decrypted.
- **Integrity:** Hash‑chained **per‑election** ledger with optional Ed25519 signatures and Merkle checkpoints.
- **Anti‑replay:** One‑Time Voting Token (**OVT**, server‑signed, one‑use) + idempotent `vote_id`.
- **Unlinkability:** No identity data in the vote pipeline (ciphertexts + tokens only).

## 1) High‑Level Architecture

```
[Booth App (Tkinter, kiosk)]                 [Flask Server (service user)]       [SQLite]        [Ledger Files]
  • Face Auth UI + Liveness                    • Auth Service (face pass → OVT)     voters               /ledger/EL-*/ledger.jsonl
  • Ballot Builder (Paillier PK)               • Vote Ingest (exactly-once)         elections           /ledger/EL-*/anchors/*
  • Client Hash (SHA-256)                      • Crypto/Tally (Paillier SK)         voter_election_status
  • Local Queue (sqlite outbox)                • Ledger Service (hash chain)        ovt_tokens          /proof/EL-*/...
  • HTTPS to localhost                         • Admin Console (web UI)             encrypted_votes
                                              • Audit Logger                        ledger_blocks (mirror)
                                                                                    audit_log
```

**Local transport:** HTTPS
**Remote‑ready:** Replace localhost with TLS + mTLS, device certificates, same APIs.

## 2) Components & Responsibilities

- **Booth App (Tkinter):** Voter UX; face auth with liveness; requests OVT; encrypts ballot (Paillier PK); computes `client_hash`; pushes `/votes`; retries via local outbox. **On startup, the Booth queries the server for the currently OPEN election_id. If none, it refuses to start the voting flow.**
- **Flask Server:** Validates OVT; stores ciphertext; appends to ledger (atomic with prev_hash continuity); exposes admin UI for election lifecycle; runs tally; exports proof bundle.
- **DB (SQLite):** Authoritative store for voters, election state, encrypted votes, OVT tokens, mirrored ledger blocks, audit logs.
- **Ledger (Per‑Election):** Append‑only JSONL file per election with chained block hashes; periodic Merkle checkpoints; optional Ed25519 signatures; anchored snapshots.
- **Admin Console:** Create/open/close elections; enroll/approve voters; monitor health; verify ledger; run tally; export proofs; archive.
- **Auditor Console** Allow auditors to independently verify elections, proof bundles, ledgers, and tally results without admin privileges. (read only)

## 3) Trust Model & Keys

#### Paillier (Ballot Encryption)

- **PK_paillier (public)**: Deployed to Booth apps. Used by voters to encrypt ballots.
- **SK_paillier (private)**: Held only on the Server. Used at tally to decrypt and compute results.

#### OVT Signing (One-time Voting Tokens)

- **Server signing keypair (SK_server_sign / PK_server_sign)**:
  - **SK_server_sign**: Held on Server; used to sign OVTs.
  - **PK_server_sign**: Distributed to Booth apps; used to verify OVT signatures.
- Algorithm: **Ed25519 preferred** (RSA-2048 acceptable for fallback).

#### Ledger Integrity & Anchoring

- **Ledger signing keypair (SK_ledger_sign / PK_ledger_sign)**:
  - **SK_ledger_sign**: Held on Server; used to:
    - sign each block header (ensures blocks cannot be altered undetected),
    - sign periodic checkpoints (Merkle roots) to anchor the ledger history.
  - **PK_ledger_sign**: Published to auditors/observers; used to verify both block headers and checkpoints.
- Anchoring method: **digital signatures only** (no blockchain posting).
  - Signed checkpoints can be exported to DB, admin console, or external observers for independent verification.

#### Hashes

- **SHA-256**: Used for all fingerprints: client integrity hashes, vote hashes, block chaining, Merkle tree leaves.
- No secrets required.

## 4) Data Model

#### elections

| Column      | Type             | Description                        |
| ----------- | ---------------- | ---------------------------------- |
| election_id | TEXT PRIMARY KEY | Unique identifier for the election |
| name        | TEXT             | Election name/title                |
| status      | TEXT CHECK       | Current election state             |
| params_json | TEXT             | Election parameters/configuration  |
| created_at  | TIMESTAMP        | Creation timestamp                 |
| closed_at   | TIMESTAMP        | Closure timestamp (nullable)       |

#### candidates

| Column       | Type                        | Description                              |
| ------------ | --------------------------- | ---------------------------------------- |
| election_id  | FK → elections(election_id) | Election reference                       |
| candidate_id | PK                          | Unique candidate identifier              |
| name         | VARCHAR                     | Candidate name                           |
| meta         | JSONB                       | Optional metadata (e.g., party, profile) |

#### voters

| Column     | Type             | Description                            |
| ---------- | ---------------- | -------------------------------------- |
| voter_id   | TEXT PRIMARY KEY | Unique voter identifier                |
| face_meta  | TEXT             | Biometric or face recognition metadata |
| created_at | INTEGER          | Registration timestamp                 |
| status     | TEXT CHECK       | Voter account state                    |

#### voter_election_status

| Column       | Type                           | Description                       |
| ------------ | ------------------------------ | --------------------------------- |
| election_id  | FK → elections(election_id)    | Election reference                |
| voter_id     | FK → voters(voter_id)          | Voter reference                   |
| status       | ENUM[pending, active, blocked] | Voter’s status for this election  |
| voted_flag   | BOOL                           | True if voter has cast their vote |
| last_auth_ts | TIMESTAMP                      | Last authentication timestamp     |

#### ovt_tokens

| Column             | Type                         | Description                        |
| ------------------ | ---------------------------- | ---------------------------------- |
| ovt_uuid           | PK                           | Unique OVT token identifier        |
| election_id        | FK → elections(election_id)  | Election reference                 |
| booth_id           | VARCHAR                      | Optional booth/location identifier |
| not_before         | TIMESTAMP                    | Token valid from timestamp         |
| expires_at         | TIMESTAMP                    | Token expiration timestamp         |
| status             | ENUM[issued, spent, expired] | Current token status               |
| issued_to_voter_id | FK → voters(voter_id)        | Assigned voter                     |
| created_at         | TIMESTAMP                    | Token creation timestamp           |

#### encrypted_votes

| Column       | Type             | Description                        |
| ------------ | ---------------- | ---------------------------------- |
| vote_id      | TEXT PRIMARY KEY | Unique vote identifier             |
| election_id  | TEXT             | Election reference                 |
| ciphertext   | BLOB             | Encrypted vote data                |
| client_hash  | TEXT             | Hash from client for integrity     |
| ledger_index | INT              | Position in ledger                 |
| ts           | TIMESTAMP        | Vote timestamp                     |
| booth_id     | VARCHAR          | Optional booth/location identifier |

#### ledger_blocks

| Column       | Type                        | Description                              |
| ------------ | --------------------------- | ---------------------------------------- |
| index        | INT                         | Ledger block index                       |
| election_id  | FK → elections(election_id) | Election reference                       |
| vote_hash    | CHAR(64)                    | Hash of vote or batch                    |
| payload_meta | JSONB                       | Optional metadata for block payload      |
| prev_hash    | CHAR(64)                    | Previous block hash (chain integrity)    |
| hash         | CHAR(64)                    | Current block hash                       |
| sig          | BYTEA                       | Digital signature for block verification |
| ts           | TIMESTAMP                   | Block timestamp                          |

#### audit_log

| Column      | Type                        | Description                                  |
| ----------- | --------------------------- | -------------------------------------------- |
| id          | PK                          | Unique audit log entry identifier            |
| actor       | VARCHAR                     | User or system performing action             |
| action      | VARCHAR                     | Action performed (e.g., voter_approved)      |
| election_id | FK → elections(election_id) | Election reference                           |
| target      | VARCHAR                     | Target object (voter_id, candidate_id, etc.) |
| details     | JSONB                       | Optional additional details                  |
| ts          | TIMESTAMP                   | Timestamp of action                          |

### Guards

- All writes **must include `election_id`**.
- Constraints enforce **no cross-election references** for votes, tokens, or statuses.
- Indexes recommended on `election_id` for candidates, encrypted_votes, ledger_blocks, and voter_election_status for efficient querying.
- **Constraints (added):** `ledger_blocks` **PRIMARY KEY (election_id, index)**; **UNIQUE (election_id, hash)**; **UNIQUE (election_id, vote_hash)**. `encrypted_votes` **UNIQUE (election_id, vote_id)** and **UNIQUE (election_id, ledger_index)**. `voter_election_status` **PRIMARY KEY (election_id, voter_id)**.

## 5) Per‑Election Ledger Design

**Filesystem layout:**

```
/ledger/
  EL-2025-01/
    ledger.jsonl                 # append-only blocks (votes + checkpoints)
    anchors/                     # signed anchors per checkpoint
  EL-2025-02/
    ledger.jsonl
/proof/
  EL-2025-01/                    # proof bundle at close/tally
```

**DB partitioning:** `ledger_blocks` partitioned by `election_id`.

**Block: one vote = one block**

```json
{
  "index": 157,
  "election_id": "EL-2025-01",
  "vote_hash": "sha256(ciphertext || election_salt)",
  "payload_meta": {
    "cipher_len": 512,
    "timestamp": "2025-09-30T09:02:11Z",
    "booth_id": "B-01",
    "client_hash": "sha256(ciphertext)"
  },
  "prev_hash": "<hex>",
  "hash": "sha256(index||election_id||vote_hash||payload_meta||prev_hash)",
  "sig": "<optional Ed25519(block_header)>"
}
```

**Genesis:** index=0, `hash=sha256('GENESIS'||election_id||created_at)`. **Genesis is written at election creation (`POST /elections`)** and stores `payload_meta.election_salt` (public hex) used in `vote_hash`.

**Checkpoint (every N blocks, e.g., 50):** includes Merkle root of `vote_hashes[start..end]`. Signed; emits an **anchor** file `{last_index,last_hash,timestamp,signature}` for rollback detection.

**Append protocol (atomic):** Build → hash → optional sign → write `*.part` → fsync → rename into `ledger.jsonl` → mirror to DB inside vote TX → commit. Crash recovery replays at most one block.

**Verification:**

1. Hash chain & index monotonicity; 2) optional signature checks; 3) Merkle roots for checkpoint ranges; 4) bijection between `encrypted_votes` and ledger vote blocks by **recomputing** `vote_hash = sha256(ciphertext || election_salt)` from proof materials.

**Proof Bundle (clarified):** Includes **ledger snapshot**, **encrypted votes (ciphertexts only)**, **audit log (PII redacted)**, and **`election_salt`**. Excludes `ovt_tokens` and any voter identity data.

## 6) API Reference (Local Base: `https://localhost:8443`)

**Error Response Shape:**

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
```

**Common Error Codes:**  
`NOT_ACTIVE`, `DUPLICATE_VOTER`, `AUTH_FAIL`, `LOCKOUT`, `OVT_EXPIRED`, `OVT_SPENT`, `OVT_NOT_FOUND`, `INVALID_SIGNATURE`, `INVALID_PAYLOAD`, `PAYLOAD_TOO_LARGE`, `ELECTION_CLOSED`, `ELECTION_PAUSED`, `CHAIN_APPEND_FAILED`, `IDEMPOTENT_REPLAY`, `RATE_LIMITED`, `SERVER_BUSY`.

#### Elections (Admin)

| Endpoint                  | Method | Description                                                            |
| ------------------------- | ------ | ---------------------------------------------------------------------- |
| `/elections`              | POST   | Create DRAFT election **and write genesis** (includes `election_salt`) |
| `/elections`              | GET    | List all elections                                                     |
| `/elections/{id}`         | GET    | Get election details                                                   |
| `/elections/{id}/open`    | POST   | Set election state → OPEN                                              |
| `/elections/{id}/pause`   | POST   | Pause election                                                         |
| `/elections/{id}/resume`  | POST   | Resume paused election                                                 |
| `/elections/{id}/close`   | POST   | Close election, freeze intake                                          |
| `/elections/{id}/tally`   | POST   | Generate totals, store `tally_report.json`                             |
| `/elections/{id}/proof`   | GET    | Proof bundle metadata / download links                                 |
| `/elections/{id}/archive` | POST   | Archive election (demo-only)                                           |
| `/elections/{id}/reset`   | POST   | Reset election (demo-only)                                             |

#### Voters (Admin)

| Endpoint                     | Method | Description                                                           |
| ---------------------------- | ------ | --------------------------------------------------------------------- |
| `/voters/enroll`             | POST   | `{voter_id, face_template_meta}` → `201 {voter_id, status:"pending"}` |
| `/voters/{voter_id}/approve` | POST   | Approve voter → `200 {status:"active"}`                               |

#### Auth & OVT (Booth)

| Endpoint            | Method | Description                                                                                                                                                                                      |
| ------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/auth/face/verify` | POST   | `{pass, confidence, voter_id?}`; enforces attempts, lockout, active status                                                                                                                       |
| `/ovt/issue`        | POST   | Returns signed OVT: `{ovt:{...}, server_sig}`. If a new OVT is issued while a prior OVT is unspent, the previous token is **atomically revoked/expired**. Only the most recent OVT can be spent. |

#### Votes (Booth)

| Endpoint | Method | Description                                                                                                                                                                                                                                                                                                                                   |
| -------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/votes` | POST   | Request: `{vote_id, election_id, booth_id, ciphertext, client_hash, ovt, ts}` → Response: `{ledger_index, block_hash, ack:"stored"}`. On `/votes`, the server validates **prev_hash continuity** (and optional block signature) before appending the new block. Full ledger verification runs on demand and at **close/tally**, not per vote. |

**Server Transaction Flow:**

1. Validate OVT (signature, TTL, spent)
2. Insert vote (unique `vote_id`)
3. Mark OVT spent
4. Append ledger block
5. Mirror → Commit

**Idempotency:** Re-submitting same `vote_id` returns same ACK.

#### Ledger Utilities (Admin)

| Endpoint                       | Method | Description                                                             |
| ------------------------------ | ------ | ----------------------------------------------------------------------- |
| `/ledger/last?election_id=…`   | GET    | Returns `{index, hash}` of last block                                   |
| `/ledger/verify?election_id=…` | GET    | Returns `{ok, height, last_hash, failed_at}`; verifies ledger integrity |

---

#### Auditor (Read-Only)

| Endpoint                               | Method | Description                                |
| -------------------------------------- | ------ | ------------------------------------------ |
| `/auditor/elections`                   | GET    | List elections                             |
| `/auditor/elections/{id}/tally-report` | GET    | Final tally report (read-only)             |
| `/auditor/elections/{id}/audit-log`    | GET    | Read audit logs for `{id}` only (redacted) |

**Audit Log Example:**

```json
[
  {
    "actor": "admin1",
    "action": "voter_approved",
    "target": "voter123",
    "ts": "2025-09-30T09:05:00Z"
  },
  {
    "actor": "admin2",
    "action": "election_closed",
    "target": "EL-2025-01",
    "ts": "2025-09-30T10:00:00Z"
  }
]
```

#### Notes & Verification

- All auditor endpoints are **read-only** and scoped to one election per call.
- Verification uses public keys only:
  - `PK_ledger_sign` → verify block/anchor signatures
  - `PK_server_sign` → verify OVT format if needed
- Proof bundles contain **ledger snapshot, ciphertexts, redacted audit log, and `election_salt`**. They **exclude** `ovt_tokens` and all voter identity data.
- All endpoints enforce **cross-election isolation**

**Limits:** `ciphertext` ≤ 8KB; time skew ±120s; `/ovt/issue` rate limit per voter/session.

## 7) User Stories & Acceptance Criteria

#### Admin

**Enroll Voter**

- _Story:_ As an admin, I want to enroll a voter by verifying ID and capturing a face template.
- _Acceptance Criteria:_
  - Duplicate detection warns if voter already exists.
  - New record has `status=pending`.
  - Audit log entry is created for enrollment.

**Approve Voter**

- _Story:_ As an admin, I want to approve a pending voter.
- _Acceptance Criteria:_
  - Voter `status` changes to `active`.
  - Optional dual-control approval workflow.
  - Audit log entry is created for approval.

**Create/Manage Election**

- _Story:_ As an admin, I want to create, open, pause, resume, close, tally, or archive elections.
- _Acceptance Criteria:_
  - Election state transitions follow defined ENUM (`draft → open → paused → closed → tallied → archived`).
  - **Genesis block is written at election creation** (not on open).
  - Closed elections reject further votes (`ELECTION_CLOSED` error).
  - Audit log records all state changes.

**Tally Election**

- _Story:_ As an admin, I want to tally the votes at the end of the election.
- _Acceptance Criteria:_
  - Ledger chain verifies integrity before tallying.
  - Homomorphic sum applied; only totals decrypted.
  - Tally Report includes `{chain_last_hash, block_count}`.
  - Proof bundle available for auditors.

#### Voter

**Authenticate via Face**

- _Story:_ As a voter, I want to authenticate using my face at a booth.
- _Acceptance Criteria:_
  - Maximum 3 attempts per session.
  - Liveness detection required.
  - Lockout 60 seconds after failed attempts.
  - Audit log entry created with confidence score.

**Cast Encrypted Vote**

- _Story:_ As a voter, I want to submit my encrypted vote using an OVT token.
- _Acceptance Criteria:_
  - OVT validated for signature, TTL, and spent status.
  - Ciphertext stored in `encrypted_votes`.
  - Ledger block appended with `vote_hash = sha256(ciphertext || election_salt)`.
  - Response returns `{ledger_index, block_hash}`.
  - Re-submitting same `vote_id` returns same ACK (idempotency).

#### Booth

**Obtain OVT**

- _Story:_ As a booth operator, I want to issue a one-time voting token to a verified voter.
- _Acceptance Criteria:_
  - OVT valid only within specified time window.
  - Single-use only (`use_limit=1`).
  - **If a new OVT is issued while a prior OVT is unspent, the previous OVT is atomically revoked/expired.**
  - Server signature included for validation at vote submission.
  - Audit entry created for issuance.

#### Auditor

**Audit Election**

- _Story:_ As an auditor, I want to verify the election independently.
- _Acceptance Criteria:_
  - Can access read-only APIs: `/auditor/elections`, `/auditor/elections/{id}/tally-report`, `/auditor/elections/{id}/audit-log`.
  - Proof bundle downloaded contains votes, ledger, and audit logs plus `election_salt`.
  - Verification uses public keys only (`PK_ledger_sign`, `PK_server_sign`).
  - Cannot create or modify votes or election state.

## 8) Sequence Diagrams (ASCII)

**A) Enrollment**

```
Admin                 Server                DB
 | verify ID           |                    |
 |--capture face------>|                    |
 |                     |--POST /voters/enroll--> insert pending
 |                     |<----------------- 201
 |--approve------------> set status=active -> create audit
 |                     |<----------------- 200
```

**B) Voting**

```
Voter       Booth           Server                DB              Ledger
 |face→      |--/auth/face→ verify + rate/lockout|                |
 |           |<----pass-----|                     |                |
 |           |--/ovt/issue→ create signed OVT   -> insert OVT       |
 |           |<---OVT+sig---|                     |                |
 |select     | encrypt+hash   |                    |                |
 |           |--/votes-------> validate OVT       | insert encrypted_votes
 |           |                 mark OVT spent     | append ledger block
 |           |                 mirror + commit    |
 |           |<---ACK(index)---|                   |
```

**C) Close & Tally**

```
Admin       Server                 DB               Ledger
 |--close→  mark CLOSED            snapshot
 |<---200---|
 |--tally→  verify ledger chain → homomorphic sum → decrypt totals → store tally_report.json
 |<---report---|
 |--proof→ generate proof bundle
 |<---bundle metadata/links---|
```

**D) Audit & Proof (Auditor)**

```
Auditor    Server                 DB
 |--list→ /auditor/elections--> fetch elections
 |<---list of elections--------|
 |--view audit→ /audit-log--> fetch audit entries
 |<---audit JSON---------------|
 |--download proof→ /proof--> fetch proof bundle
 |<---bundle metadata/links----|
```

## 9) Non‑Functional Requirements (MVP targets)

- **Performance:** Auth + OVT < 2s; Submit ACK < 1s (local).
- **Resilience:** Outbox survives restarts; exactly‑once semantics from booth PoV.
- **Security:** No face images stored; no identity in vote pipeline; HTTPS; least privilege.
- **Auditability:** All admin actions logged; ledger verifiable end‑to‑end.
- **Usability:** Kiosk‑safe UI; large controls; clear error messages.

## 10) Security Model (STRIDE → Controls)

- **Spoofing:** Thresholded face match + liveness + attempts + lockout; admin oversight.
- **Tampering:** Client SHA‑256; server recompute; per‑election hash chain; signed checkpoints.
- **Repudiation:** Audit logs; booth receives immutable ledger index as receipt.
- **Info disclosure:** Paillier encryption; unlinkability via OVT; totals‑only decryption.
- **DoS:** Rate limits, bounded queues, backoff; admin pause.
- **Privilege escalation:** Separate admin console; RBAC; dual‑control for close/tally.
- **Replay/double vote:** OVT `use_limit=1` with atomic spent‑mark; idempotent `vote_id` and OVT revocation on re-issue.
- **Rollback:** Checkpoint anchors + DB mirror + last_hash snapshot.

## 11) Transactions & Atomicity

### /voters/enroll

- Single atomic transaction: insert voter + audit log.
- Duplicate voter detection enforced within the same transaction to prevent race conditions.

### /ovt/issue

- Single atomic transaction: insert OVT + audit log.
- OVT issuance respects TTL (`OVT_TTL_SECS`) and ensures **single issuance per voter per window**. **If a new OVT is issued while a prior OVT is unspent, the prior token is revoked/expired.**

### /votes (core)

- Steps (atomic): insert encrypted vote → mark OVT as spent → append ledger block (fsync+rename) → mirror → commit.
- Idempotency: repeated submissions of same `vote_id` acknowledged without re-appending.
- Ledger append failure: transaction aborts; OVT remains unspent.
- Startup repair: replays at most one block per failure.
- **On `/votes`, the server validates prev_hash continuity (and optional block signature) before append. Full chain verification runs on demand and at close/tally.**

### /elections/close

- Atomic transaction: mark election as CLOSED → snapshot `{last_index, last_hash}`.
- Ledger verification is performed before closure to ensure integrity.
- Audit log entry is created for closure action.

## 12) Configuration & Environments

### .env Keys (local)

- `MODE=LOCAL`
- `CHECKPOINT_INTERVAL=50`
- `OVT_TTL_SECS=300`
- `OVT_RECENT_AUTH_WINDOW_SECS=60`
- `LOCKOUT_SECS=60`
- `HASH_ALGO=SHA256`
- `LEDGER_SIGNING=true`
- `RATE_LIMIT=10` # max requests per second per voter/booth

### Directory Permissions

- `ledger/*` → 700
- `anchors/*` → 700
- `audit/*` → 700
- keys → 600
- Only the server process has read/write access to sensitive directories.

### Notes

- All sensitive operations rely on atomic filesystem writes and database transactions.
- Config values can be tuned for deployment environment; production may increase `CHECKPOINT_INTERVAL` and reduce TTLs for performance/security trade-offs.

## 13) Testing Strategy

**Unit Tests:**

- Verify **signatures**, **hash recomputations**, **Merkle root correctness**.
- Validate **OVT TTL**, **use-limit enforcement**, and **idempotency** of `vote_id`.

**Integration Tests:**

- Simulate **crash scenarios** between file append and DB commit; verify repair logic.
- Check **ledger chain verification** across checkpoints.

**End-to-End (E2E) Tests:**

- Happy path: normal voting from auth → OVT → cast vote → ledger append.
- Lockout path: test max attempts for face auth.
- Network down / retry: ensure outbox mechanism works.
- Duplicate submissions: same `vote_id` acknowledged, no double append.

**Security Tests:**

- Replay `/votes` requests with same or different `vote_id`.
- Attempt to mutate or truncate the ledger file.
- Submit votes with **invalid OVT signatures**.

**Performance Tests:**

- Measure **latency envelopes** for `/auth`, `/ovt/issue`, and `/votes` endpoints.
- Ensure system meets expected throughput under concurrent voters.

**Explanation in Simple Terms:**

- Unit tests check **individual pieces** (OVT, ledger hash, signature).
- Integration tests check **how components work together**, especially under crash/recovery.
- E2E tests simulate **real voter experience** including retries and duplicates.
- Security tests try **attacks** (replay, tamper) to ensure safety.
- Performance tests ensure **system is fast and responsive**.

## 14) Demo Working

1. **Create election (DRAFT)** → add candidates → **Open election** (**genesis ledger already exists** from creation).
2. **Enroll + approve** 2 voters.
3. From **booth**: authenticate → request OVT → cast 2–3 votes. Show **ledger height** & **last_hash**.
4. Run **Ledger Verify** mid-election → confirm **checkpoint** exists.
5. **Close election** → demonstrate `/votes` endpoint now rejects submissions.
6. **Tally** election → display totals + ledger chain metadata.
7. **Export Proof Bundle** → open and inspect the files (bundle includes `election_salt`).

**Explanation in Simple Terms:**

- Walkthrough shows **full system flow** from creating election to generating proofs.
- Demonstrates **voter, booth, admin, ledger, and auditor interactions**.
- Includes **mid-election checks** to validate system integrity.

## 15) Operations Runbook (Local)

**Start System:**

1. Start **database**.
2. Start **Flask server** (admin UI).
3. Start **Booth app** (for OVT & voting).

**Backup (post-close):**

- Backup **DB dump**, `ledger/EL-*`, and `proof/EL-*` directories.
- **Do not rotate keys mid-election**; keep current signing keys until election fully archived.

**Crash Recovery:**

- On server restart, run `ledger/verify`.
- If a file block exists without DB mirror → **replay that block**.
- If ledger chain is broken → **halt and raise incident**.

**Ledger & Key Rotation:**

- New election → create **new ledger folder**.
- Start **fresh OVT signing epoch** to isolate from previous election.

**Explanation in Simple Terms:**

- This runbook helps admins **start, backup, recover, and rotate** elections safely.
- Ensures ledger integrity and OVT consistency.
- Protects keys and election data from accidental loss or corruption.

## 16) Glossary

- **OVT:** One‑Time Voting Token; signed capability for a single vote.
- **Client Hash:** SHA‑256 of ciphertext sent by booth for integrity check.
- **Vote Hash:** SHA‑256 of `(ciphertext || election_salt)`; block identity.
- **Checkpoint:** Special block summarizing a range via Merkle root; signed; anchored.
- **Anchor:** Small signed snapshot `{index, hash, ts}` stored separately to detect truncation.
