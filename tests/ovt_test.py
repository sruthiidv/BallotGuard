from server_backend.crypto.ovt import generate_ovt, sign_ovt, verify_ovt

# --- Step 1: Generate a random one-time token ---
token = generate_ovt()
print("OVT token:", token)

# --- Step 2: Server signs the token ---
signature = sign_ovt(token)
print("Signature:", signature.hex())

# --- Step 3: Client verifies the token ---
is_valid = verify_ovt(token, signature)
print("Verification result:", is_valid)  # Should be True
