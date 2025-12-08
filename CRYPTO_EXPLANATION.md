# 🔐 Cryptography Choices Explained

## Why These Schemes and Not Simple Integers?

---

## 1. PAILLIER HOMOMORPHIC ENCRYPTION (Not Simple Integer Encryption)

### ❌ What We DON'T Use: Simple Integer Encryption

```python
# Simple approach (INSECURE):
encrypted_vote = (vote_value * secret_key) % prime
decrypted_vote = (encrypted_vote * inverse_key) % prime

# Problems:
# 1. Server needs secret key to decrypt → sees individual votes
# 2. Cannot add encrypted values → must decrypt each vote
# 3. All voters share same key → anyone with key can decrypt all votes
# 4. No semantic security → patterns visible
```

### ✅ What We USE: Paillier Homomorphic Encryption

```python
# Paillier approach (SECURE):
encrypted_vote = paillier_encrypt(public_key, 1)  # Encrypt value 1
sum_encrypted = enc1 + enc2 + enc3  # Add in encrypted space!
total = paillier_decrypt(private_key, sum_encrypted)  # Decrypt only total

# Benefits:
# 1. Server NEVER sees individual votes
# 2. Can tally votes while encrypted (homomorphic addition)
# 3. Only election authority has private key
# 4. Probabilistic: same vote = different ciphertext each time
```

### Why Homomorphic Encryption Matters:

```
SCENARIO: 3 voters vote for Candidate A

Without Homomorphic Encryption:
  Server decrypts: Vote 1 = A, Vote 2 = A, Vote 3 = A
  → Privacy VIOLATED (server knows individual choices)

With Paillier:
  Server sees: Enc(1) + Enc(1) + Enc(1)
  Server computes: Enc(1 + 1 + 1) = Enc(3)
  Server decrypts: Total = 3
  → Privacy PRESERVED (only total known, not individuals)
```

**Key Size:** 2048 bits (modulus n)
**Security Level:** Equivalent to RSA-2048
**Property:** Additive homomorphism: Enc(a) \* Enc(b) = Enc(a + b)

---

## 2. RSA-PSS SIGNATURES (Not HMAC or Simple Hashing)

### ❌ What We DON'T Use: HMAC (Symmetric)

```python
# HMAC approach (WRONG FOR THIS USE CASE):
signature = hmac(secret_key, message)
verify = hmac(secret_key, message) == signature

# Problems:
# 1. Verifier needs same secret_key as signer
# 2. Cannot distribute verification key publicly
# 3. Anyone who can verify can also forge signatures
# 4. No non-repudiation (anyone with key can claim they signed)
```

### ❌ What We DON'T Use: Simple Hash

```python
# Simple hash (INSECURE):
signature = sha256(message)
verify = sha256(message) == signature

# Problems:
# 1. Anyone can compute same hash
# 2. No proof of WHO created the signature
# 3. Trivial to forge (just hash the message)
# 4. No authentication
```

### ✅ What We USE: RSA-PSS (Asymmetric Signature)

```python
# RSA-PSS approach (SECURE):
signature = rsa_private_key.sign(sha256(message))
valid = rsa_public_key.verify(signature, sha256(message))

# Benefits:
# 1. Only holder of private key can sign
# 2. Anyone with public key can verify
# 3. Cannot forge without private key
# 4. Non-repudiation: only server could have signed
# 5. PSS padding: probabilistic, more secure than PKCS#1 v1.5
```

### Why Asymmetric Signatures Matter:

```
SCENARIO: Server issues OVT token to voter

With HMAC (symmetric):
  Server: signature = hmac(secret_key, ovt_token)
  Client: verify = hmac(secret_key, ovt_token)
  → Problem: Client has secret_key, can forge OVT tokens!

With RSA-PSS (asymmetric):
  Server: signature = rsa_sign(private_key, ovt_token)
  Client: valid = rsa_verify(public_key, signature)
  → Solution: Client can verify but NOT forge!
```

**Key Size:** 3072 bits (for receipts), 2048 bits (for OVT/blocks)
**Hash:** SHA-256
**Padding:** PSS (Probabilistic Signature Scheme)
**Security:** Computationally infeasible to forge without private key

---

## 3. SHA-256 HASHING (Not MD5 or CRC32)

### ❌ What We DON'T Use: MD5 (Broken)

```python
# MD5 approach (INSECURE):
hash = md5(vote_data)

# Problems:
# 1. Collision attacks found (can create two votes with same hash)
# 2. Cryptographically broken since 2004
# 3. Not suitable for security-critical applications
# 4. Only 128-bit output (too small)
```

### ❌ What We DON'T Use: CRC32 (Not Cryptographic)

```python
# CRC32 approach (NOT FOR SECURITY):
hash = crc32(vote_data)

# Problems:
# 1. Not cryptographically secure (designed for error detection)
# 2. Easy to find collisions
# 3. Only 32-bit output
# 4. No preimage resistance
```

### ✅ What We USE: SHA-256 (Secure Hash Algorithm)

```python
# SHA-256 approach (SECURE):
hash = sha256(vote_data)

# Benefits:
# 1. Collision-resistant (computationally infeasible to find two inputs with same hash)
# 2. Preimage-resistant (can't reverse hash to find original)
# 3. Avalanche effect (tiny change = completely different hash)
# 4. 256-bit output (2^256 possible values)
# 5. Industry standard, thoroughly analyzed
```

### Why SHA-256 Matters:

```
SCENARIO: Blockchain integrity verification

With CRC32 (weak):
  Block 1: CRC32 = 0x1A2B3C4D
  Attacker modifies block, adjusts padding to get same CRC
  → Tamper NOT detected!

With SHA-256 (strong):
  Block 1: SHA-256 = a4f3c2b8...
  Attacker modifies block
  → Computationally infeasible to find modified block with same hash
  → Tamper DETECTED!
```

**Output Size:** 256 bits (64 hexadecimal characters)
**Collision Resistance:** 2^128 operations to find collision (infeasible)
**Preimage Resistance:** 2^256 operations to reverse (impossible)

---

## 4. EUCLIDEAN DISTANCE (Face Recognition)

### ❌ What We DON'T Use: Pixel-by-pixel Comparison

```python
# Simple pixel comparison (UNRELIABLE):
match = (image1 == image2).all()

# Problems:
# 1. Different lighting = no match
# 2. Different angle = no match
# 3. Different expression = no match
# 4. Glasses, makeup = no match
```

### ✅ What We USE: Deep Learning Embeddings + Euclidean Distance

```python
# CNN embedding approach (ROBUST):
embedding1 = face_recognition.face_encodings(image1)  # 128-D vector
embedding2 = face_recognition.face_encodings(image2)  # 128-D vector
distance = euclidean_distance(embedding1, embedding2)
match = (distance < 0.5)  # Threshold

# Benefits:
# 1. Lighting-invariant (CNN trained on millions of faces)
# 2. Pose-invariant (small angle changes tolerated)
# 3. Expression-invariant (smile vs. neutral face)
# 4. Robust to minor appearance changes
```

**Embedding Size:** 128 dimensions (floating-point vector)
**Distance Metric:** Euclidean (L2 norm)
**Threshold:** 0.5 (lower = more similar)
**Model:** dlib ResNet-based CNN

---

## COMPARISON TABLE

| **Need**                | **Wrong Choice**       | **Why Wrong**                    | **Right Choice**    | **Why Right**                        |
| ----------------------- | ---------------------- | -------------------------------- | ------------------- | ------------------------------------ |
| **Vote Privacy**        | RSA encryption of vote | Server decrypts individual votes | Paillier encryption | Tally without decrypting individuals |
| **Vote Tallying**       | Decrypt each vote      | No privacy                       | Homomorphic sum     | Privacy-preserving aggregation       |
| **Authentication**      | HMAC                   | Verifier can forge               | RSA-PSS             | Only signer can create               |
| **Public Verification** | Symmetric key          | Key distribution problem         | Public key crypto   | Distribute public key safely         |
| **Hash Security**       | MD5                    | Collision attacks                | SHA-256             | Collision-resistant                  |
| **Integrity**           | CRC32                  | Not cryptographic                | SHA-256             | Tamper-evident                       |
| **Face Matching**       | Pixel comparison       | Brittle                          | CNN embeddings      | Robust to variations                 |

---

## EXAMPLE OUTPUT (What You'll See)

### When Voting:

```
🔐 PAILLIER ENCRYPTION:
  Candidate: David Miller (ID: C1)
  Plaintext vote value: 1
  Public key modulus (n): 352792853755612529815384190864030126016714885680852776087314...
  Ciphertext: 12649387562938475629384756293847562938475629384756293847562938...
  Ciphertext length: 617 digits
  Exponent: -123
  Algorithm: Paillier (Homomorphic)
  Key size: ~2048 bits
  Property: Enc(1) + Enc(1) = Enc(2) without decryption
```

### When Server Signs OVT:

```
🔐 OVT SIGNING:
  Token UUID: c4f2a8b3d5e6f7a8b9c0d1e2f3a4b5c6
  Data to sign: {"election_id":"EL-2025-01","expires_at":1699632300.123,"ovt_uuid":"c4f2a8b3d5e6f7a8b9c0d1e2f3a4b5c6","voter_id":"VID-123"}
  Signature (base64): MEUCIQDx2y3z4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d...
  Signature length: 512 chars
  Algorithm: RSA-PSS with SHA-256
  Key size: 3072 bits
```

### When Creating Block:

```
🔗 BLOCKCHAIN BLOCK CREATION:
  Block index: 1
  Previous hash: GENESIS
  Vote hash: a4f3c2b8d1e5f6a7b8c9d0e1f2a3b4c5...
  Timestamp: 1699632000.123456
  Block hash (SHA-256): b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6
  Chain property: This block links to previous via prev_hash
  Tamper detection: Changing any field changes block_hash
```

### When Verifying Receipt:

```
🔐 RECEIPT VERIFICATION:
  Receipt data: {'vote_id': 'V-abc123', 'election_id': 'EL-2025-01', 'ledger_index': 1, 'block_hash': 'b5c6d7...'}
  Signature (base64): MEUCIQDx2y3z4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d...
  Algorithm: RSA-PSS with SHA-256
  Verifying with server's public key...
  ✅ VERIFICATION PASSED!
  Receipt is authentic and came from legitimate server
```

---

## WHY NOT SIMPLER APPROACHES?

### "Why not just encrypt with a password?"

❌ Password encryption (AES with password):

- Password must be shared with everyone who needs to decrypt
- Anyone with password can decrypt all votes
- No homomorphic properties
- Password compromise = all votes exposed

✅ Paillier with public/private keys:

- Public key for encryption (can share widely)
- Private key for decryption (only election authority)
- Homomorphic tallying
- Individual votes never exposed

### "Why not just use a hash for signatures?"

❌ Hash-based "signature":

- Anyone can compute same hash
- No authentication (can't prove who created it)
- Trivial to forge

✅ RSA digital signatures:

- Only private key holder can create
- Public key allows verification
- Cryptographically secure
- Non-repudiation

### "Why not just store votes as integers in database?"

❌ Plaintext integers:

- Database admin sees all votes
- Server logs show all votes
- No privacy whatsoever
- Violates secret ballot principle

✅ Encrypted ciphertexts:

- Database admin sees only random numbers
- Server never sees vote choices
- Privacy preserved
- Secret ballot maintained

---

## SECURITY GUARANTEES

| **Property**    | **Guaranteed By**        | **Prevents**                          |
| --------------- | ------------------------ | ------------------------------------- |
| Vote Privacy    | Paillier encryption      | Server/admin seeing individual votes  |
| Vote Integrity  | SHA-256 hashing          | Tampering with votes after submission |
| Chain Integrity | SHA-256 block linking    | Modifying past blocks                 |
| Authentication  | RSA-PSS signatures       | Forged receipts/tokens                |
| Non-repudiation | RSA asymmetric keys      | Server denying issued receipts        |
| Unlinkability   | Probabilistic encryption | Linking votes to voters               |
| Tamper Evidence | Blockchain + hashing     | Hidden modifications                  |

---

**Bottom line:** We use these specific cryptographic schemes because they provide mathematical guarantees that simpler integer-based or hash-based approaches cannot provide. Each scheme is the industry-standard solution for its specific security need.
