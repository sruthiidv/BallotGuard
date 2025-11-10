# Keys for BallotGuard

This folder holds cryptographic keys used by the app (Paillier keys, signing keys, receipts, etc.).

IMPORTANT: Do NOT commit private keys to the repository. This folder is added to `.gitignore` and should remain local only.

Templates
---------
- `paillier_public.json` - public key for Paillier (can be stored in repo if you want, but keep private keys out).
- `paillier_private.json` - PRIVATE key: never commit. Keep locally or in a secure secrets manager.
- `receipt_public.pem` - public key for receipts (OK to share publicly).
- `receipt_private.pem` - PRIVATE signing key: never commit.

Where to place keys
-------------------
Place the real key files in one of the following locations (preferred location for the server is shown):

1) Server-local keys (preferred for server runtime):

```
BallotGuard/
  server/
    keys/
      paillier_private.json
      paillier_public.json
      receipt_private.pem
      receipt_public.pem
```

2) Project-root keys (convenient for some dev workflows):

```
BallotGuard/
  keys/
    paillier_private.json
    paillier_public.json
    receipt_private.pem
    receipt_public.pem
```

Notes:
- The server code currently looks for keys in `server/keys/` by default (`server/server_config.py`).
- If you prefer to keep keys in the project root `keys/`, you can either copy them into `server/keys/` or create a local symlink.

How the app loads keys
----------------------
- The server and some helper scripts look for keys in `./keys/paillier_private.json` and `./keys/paillier_public.json`.
- The admin/voter UIs load `receipt_public.pem` (and server uses `receipt_private.pem` for signing receipts).

Best practices
--------------
- Use environment variables or a secrets manager (e.g., Vault, GitHub Secrets for CI) for private keys in CI/CD.
- If a private key is accidentally committed, rotate/regenerate it immediately and remove it from Git history (use `git filter-repo` or `git filter-branch`).

Example commands (local dev)
----------------------------
- To run the Admin UI (PowerShell helper):

```powershell
.\run_admin.ps1
```

- To run the Voter UI (PowerShell helper):

```powershell
.\run_voter.ps1
```

- If you installed the package (`pip install -e .`), you can use the console scripts:

```powershell
run-admin
run-voter
```
