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

# BallotGuard Voting System

## Overview
BallotGuard is a modular digital voting system with a modern CustomTkinter UI, face verification, and cryptographic vote handling. This project is structured for easy development and extension.

## Prerequisites
- Python 3.10+
- All dependencies in `requirements.txt`

## Installation
1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd BallotGuard
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Running the Application
1. Start the server (in a new terminal):
   ```sh
   python simple_server.py
   ```
2. Start the client app:
   ```sh
   python client_app/voting/app.py
   ```

## Usage
- On launch, select your role (Voter, Admin, Auditor).
- Voters can register, verify face, and vote in open elections.
- Admin and Auditor features are placeholders for future development.

## Notes
- No `setup.py` is required unless you want to distribute as a pip package. For running as an app, just use the above commands.
- All local/temporary files, caches, and environments are ignored via `.gitignore`.
- Face verification is currently mocked on the server for demo purposes.

---

**For development or deployment, just use `python client_app/voting/app.py` to launch the UI.**
