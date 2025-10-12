from phe import paillier
import json
from pathlib import Path

# Set keys directory
KEYS_DIR = Path(__file__).resolve().parent / "server" / "keys"
KEYS_DIR.mkdir(parents=True, exist_ok=True)

# Generate Paillier keypair
public_key, private_key = paillier.generate_paillier_keypair()

# Save public key (n)
pub = {"n": public_key.n}
with open(KEYS_DIR / "paillier_public.json", "w", encoding="utf-8") as f:
    json.dump(pub, f, indent=2)

# Save private key (p, q)
priv = {"p": private_key.p, "q": private_key.q}
with open(KEYS_DIR / "paillier_private.json", "w", encoding="utf-8") as f:
    json.dump(priv, f, indent=2)

print("Paillier keys generated and saved in 'server/keys'.")
