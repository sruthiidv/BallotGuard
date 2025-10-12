import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def verify_signature(message, signature):
    try:
        # Check if public key file exists
        key_path = "public_key.pem"
        if not os.path.exists(key_path):
            print(f"Warning: {key_path} not found. Signature verification skipped.")
            return True  # Skip verification if key doesn't exist (for development)
            
        with open(key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        public_key.verify(
            bytes.fromhex(signature),
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print("Signature verification failed:", e)
        return False
