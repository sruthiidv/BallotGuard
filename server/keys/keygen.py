# pip install pycryptodome
from Crypto.PublicKey import RSA
from pathlib import Path
import hashlib, base64

OUT_DIR = Path(__file__).resolve().parent / "server" / "keys"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def sha256_fingerprint(pem: bytes) -> str:
    h = hashlib.sha256(pem).digest()
    return base64.b16encode(h).decode("ascii")

def main():
    key = RSA.generate(3072)  # 2048 is fine too; 3072 for extra margin
    priv_pem = key.export_key(format="PEM", pkcs=8)       # PKCS#8
    pub_pem  = key.publickey().export_key(format="PEM")   # SubjectPublicKeyInfo

    (OUT_DIR / "receipt_private.pem").write_bytes(priv_pem)
    (OUT_DIR / "receipt_public.pem").write_bytes(pub_pem)

    print("Wrote:")
    print(f"  {OUT_DIR/'receipt_private.pem'}")
    print(f"  {OUT_DIR/'receipt_public.pem'}")

    print("\nFingerprints (pin these):")
    print("  SHA256(pub) =", sha256_fingerprint(pub_pem))
    print("  SHA256(priv) =", sha256_fingerprint(priv_pem))

if __name__ == "__main__":
    main()
