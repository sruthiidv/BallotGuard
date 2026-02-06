BallotGuard: Face-Authenticated Blockchain-Inspired Secure Voting System

BallotGuard is a research prototype of a cryptographically secure electronic voting system designed for controlled, small-scale environments such as university student elections.

It combines:

\- Client-side Paillier homomorphic encryption (3072-bit) for privacy-preserving vote tallying

\- RSA-PSS digital signatures (3072-bit) for receipt authenticity and token validation

\- One-time voting tokens (OVTs) with HMAC-SHA256 commitments for single-use enforcement and identity-vote decoupling

\- Lightweight SHA-256 hash-chained ledger for tamper-evident vote storage

\- Facial recognition with blink-based liveness detection for biometric authentication

Performance (measured on Intel i7-12700H, 16 GB RAM):

~5-second end-to-end vote submission per voter

Tallying 1000 votes in under 30 seconds

Important: This is a research/academic prototype — not suitable for real or binding elections. It has known limitations (see below) and must not be used in production without independent security audits, major hardening, and regulatory compliance.

Features

Privacy-preserving tallying via Paillier homomorphic encryption

Biometric authentication: face recognition (dlib ResNet-34) + blink liveness (EAR-based) + 3-failure lockout

Identity-vote decoupling using OVTs + HMAC commitments

Tamper-evident append-only ledger with RSA-PSS signed blocks

Signed receipts for voter submission proof

Security measures: AES-256-GCM encrypted biometrics, HTTPS/TLS, rate limiting, audit logging

STRIDE threat analysis: resists ballot stuffing, replay, manipulation, and insider risks

Full client-server implementation: Tkinter GUI (voter), Flask backend, SQLite storage, admin/audit dashboards

Architecture Overview

Client — Tkinter + CustomTkinter GUI, OpenCV + dlib for face/liveness, client-side Paillier encryption

Backend — Flask REST API (21 endpoints), OVT issuance/validation, vote ingestion, ledger management

Ledger — Custom SHA-256 hash chain in SQLite (blocks signed with RSA-PSS)

Admin/Audit — ttkbootstrap dashboard for election control + read-only audit interface

Workflow:

Voter Enrollment → Face Authentication → OVT Issuance → Vote Encryption → Ledger Append → Homomorphic Tallying → Audit Verification

Limitations & Security Caveats

Research prototype only — no formal third-party audit

Blink liveness is client-side → vulnerable to advanced deepfakes/replays

Admin dashboard lacks authentication → serious risk if server is exposed

Voter identity linked to encrypted face encodings in DB

Single-server design → no high availability or large-scale support

No full end-to-end verifiability (proof of inclusion in tally)

No coercion resistance in unsupervised/remote scenarios

Requirements

Python 3.11+

Dependencies (requirements.txt):

flask, flask-cors, flask-limiter

pycryptodome, phe (Paillier)

opencv-python, dlib, numpy

customtkinter, ttkbootstrap, pillow

requests

Installation & Quick Start

1\. Clone the repo

git clone https://github.com/YOUR-USERNAME/BallotGuard.git

cd BallotGuard

2\. Install dependencies

pip install -r requirements.txt

3\. (Optional) Install dlib with CUDA for faster face processing

(Follow platform-specific dlib installation guide)

4\. Start the backend

python backend/app.py

5\. Launch the voter client

python client/voter\_client.py

6\. Access admin/audit interface

Open admin/admin\_dashboard.html or run the admin script

See docs/SETUP.md for database initialization, election creation, and full configuration.

Repository Structure

BallotGuard/

├── backend/ # Flask server, API, ledger logic

├── client/ # Tkinter voter GUI

├── admin/ # Admin & audit dashboard

├── docs/ # Setup guide, diagrams, paper draft

├── database/ # SQLite schema & examples

├── requirements.txt

└── README.md

License

MIT License — see LICENSE for details.

Disclaimer

This software is for academic research and experimentation only. It is not secure enough for real elections. Use at your own risk.
