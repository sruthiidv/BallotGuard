<<<<<<< HEAD
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
=======
Face-Verified Blockchain-Inspired Secure Voting System
Functionalities
•	Voter Registration – Capture and store voter face data securely.
•	Face Authentication – Verify voter before unlocking voting screen.
•	Vote Casting – Candidate selection via Tkinter GUI.
•	Cryptographic Security – Digital signature, homomorphic encryption, and hashing of votes.
•	Blockchain Audit Trail – Append vote hash to blockchain ledger for tamper-proofing.
•	Admin Panel – Verify signatures, tally votes using homomorphic addition, decrypt only the final total.
>>>>>>> bbc10a79e9e59639587a69e373af4a6afe1b3d84
