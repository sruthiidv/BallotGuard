🧩 BallotGuard — Cryptography & Blockchain Module
👤 Author: Person 2
🧭 Modules:

client_app/crypto/

server_backend/crypto/

server_backend/blockchain/

🔐 Overview

This module implements all cryptographic and blockchain operations for secure, verifiable, and privacy-preserving e-voting in BallotGuard.
It ensures that votes are encrypted, authenticated, tamper-proof, and tallied securely.

⚙️ Components
1. client_app/crypto/paillier_crypto.py

Uses Paillier encryption to secure each vote.

Supports multi-candidate voting (encrypts each candidate’s vote).

Uses server’s public Paillier key (PK_paillier) for encryption.

Voter never has access to private keys.

2. server_backend/crypto/paillier_crypto.py

Generates and stores Paillier keypair:

PK_paillier (public) → shared with clients

SK_paillier (private) → server-only, used for final decryption

Performs homomorphic tallying of encrypted votes.

3. server_backend/crypto/ovt_crypto.py

Implements RSA-based OVT (One-time Voting Token) signing and verification.

Server: signs tokens using SK_server_sign.

Client: verifies tokens using PK_server_sign.

Prevents multiple votes from a single voter.

4. server_backend/crypto/ledger_crypto.py

Signs blockchain block headers with RSA (SK_ledger_sign).

Anyone can verify using PK_ledger_sign.

Protects the integrity of blockchain blocks and checkpoint exports.

5. server_backend/crypto/hash_utils.py

Provides SHA-256 hashing functions for:

Vote hashes

Block linking

Merkle tree generation

6. server_backend/blockchain/blockchain.py

Implements a lightweight append-only blockchain ledger:

Each block stores encrypted vote hashes.

Blocks linked by SHA-256 previous hashes.

Each block signed with RSA ledger key for authenticity.

Includes Merkle tree for verifying individual vote inclusion.

🔑 Key Summary
Key	Location	Purpose
PK_paillier	Client + Server	Encrypt votes
SK_paillier	Server only	Decrypt tallies
SK_server_sign	Server only	Sign OVTs
PK_server_sign	Client	Verify OVTs
SK_ledger_sign	Server only	Sign blockchain blocks
PK_ledger_sign	Public (auditors)	Verify ledger
📦 Dependencies

Add these in your requirements.txt:

cryptography==43.0.0
phe==1.5.0


Optional (for integration with Flask server):

Flask==3.0.3
Flask-Cors==4.0.0
SQLAlchemy==2.0.32
psycopg2-binary==2.9.9

🔄 Vote Flow Summary

Server generates keys and distributes public keys.

Client verifies OVT → encrypts vote → submits to server.

Server verifies OVT → stores encrypted vote → appends hash to blockchain.

At tally time, server decrypts all encrypted votes using Paillier private key and publishes signed results.