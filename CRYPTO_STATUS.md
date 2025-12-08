# BallotGuard Cryptography Status

## ✅ REQUIRED Dependencies (NO FALLBACK)

### 1. PyCryptodome (RSA-PSS Signatures)
**Status:** ✅ REQUIRED - No fallback allowed  
**Usage:**
- OVT token signing (server → client)
- Vote receipt signing (server → client)
- Block header signing (blockchain integrity)
- Signature verification (client verifies OVT, admin verifies blocks)

**Import:**
```python
from Crypto.Signature import pss
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
```

**If Missing:** Server will CRASH on startup with ImportError

---

## ⚠️ OPTIONAL Dependencies (Fallback Available)

### 1. face_recognition + dlib (Biometric Authentication)
**Status:** ⚠️ OPTIONAL - Fallback to NumPy distance  
**Primary Use:** Real CNN-based face recognition with dlib
**Fallback:** Simple Euclidean distance using NumPy

**Why Fallback Exists:**
- `dlib` is heavy dependency (~100MB)
- Requires C++ compiler on some systems
- For development/demo, simple distance works

**Detection Code:**
```python
try:
    import face_recognition
    FACE_RECOG_AVAILABLE = True
except:
    # Use _FallbackFaceRecog with numpy.linalg.norm
    FACE_RECOG_AVAILABLE = False
```

**Fallback Implementation:**
```python
class _FallbackFaceRecog:
    @staticmethod
    def compare_faces(known_encodings, probe_encoding, tolerance=0.6):
        probe = np.asarray(probe_encoding, dtype=float)
        results = []
        for k in known_encodings:
            k_arr = np.asarray(k, dtype=float)
            dist = np.linalg.norm(k_arr - probe)  # Euclidean distance
            results.append(dist <= tolerance)
        return results
```

**Impact:**
- ✅ Acceptable for research prototype
- ❌ NOT suitable for production (less accurate)
- Fallback is documented in IEEE paper Section VII.E

---

## 📊 Detailed Logging Output

When you run the server and client, you'll see these log messages:

### Server Logs (server.py)

```
[CRYPTO] ✓ Signed 256 bytes -> signature dGVzdGluZzEyMzQ1Njc4OTBhYmNk...
[CRYPTO] Signing block #5 header...
[CRYPTO] ✓ Block #5 signature VALID
[CRYPTO] ✗ Block #8 signature INVALID: ValueError('Incorrect signature')

[AUTH] Face verification: voter_id=V12345, result=PASS, confidence=0.892, total_attempts=1
[AUTH] Face verification: voter_id=V12345, result=FAIL, confidence=0.342, total_attempts=2
[AUTH] ⚠ LOCKOUT: Voter V12345 locked for 847s (failed attempts: 3)

[OVT] Issuing OVT for voter_id=V12345, election_id=EL-2025-01, ovt_uuid=abc123...
[OVT] ✓ OVT signed and ready for client

[VOTE] Signing blockchain block for vote_id=VOTE-xyz, ledger_index=42
[VOTE] ✓ Block signature stored in database

[RECEIPT] Generating signed receipt for vote_id=VOTE-xyz
[RECEIPT] ✓ Receipt signed and ready for client
```

### Client Logs (api_client.py)

```
[CLIENT] Verifying OVT signature for ovt_uuid=abc123...
[CLIENT] ✓ Signature verification PASSED (256 bytes verified)
[CLIENT] ✓ OVT signature verified successfully - token is authentic

[CLIENT] ✗ Signature verification FAILED: ValueError('Invalid signature')
[CLIENT] ✗ SECURITY ALERT: OVT signature verification FAILED!
[CLIENT] ⚠ WARNING: OVT response missing signature field
[CLIENT] ✗ ERROR: No server public key available, cannot verify signature
```

---

## 🔍 How to Verify Crypto is Working

### Method 1: Check Terminal Output

**Look for these messages:**
1. `[CRYPTO] ✓ Signed` - RSA-PSS signing is working
2. `[CLIENT] ✓ Signature verification PASSED` - Client verification working
3. `[VOTE] ✓ Block signature stored` - Blockchain signing working

**If you see these, crypto is NOT working:**
- `WARNING: Crypto not available` (old fallback message - should NOT appear)
- ImportError on startup
- No `[CRYPTO]` logs

### Method 2: Check Database

Run this SQL query to verify block signatures are being stored:
```sql
SELECT election_id, ledger_index, 
       substr(signature, 1, 32) as sig_preview,
       length(signature) as sig_length
FROM ledger_blocks 
WHERE signature IS NOT NULL
LIMIT 5;
```

**Expected:** Signatures should be ~512 characters (384 bytes base64-encoded RSA-PSS)

### Method 3: Test Authentication Lockout

1. Try face verification with wrong photo 3 times
2. **Expected output:**
   ```
   [AUTH] Face verification: voter_id=V001, result=FAIL, confidence=0.234, total_attempts=1
   [AUTH] Face verification: voter_id=V001, result=FAIL, confidence=0.189, total_attempts=2
   [AUTH] Face verification: voter_id=V001, result=FAIL, confidence=0.301, total_attempts=3
   [AUTH] ⚠ LOCKOUT: Voter V001 locked for 900s (failed attempts: 3)
   ```
3. 4th attempt should return HTTP 429 with lockout message

### Method 4: Test OVT Signature Verification

**Modify client to inject bad signature:**
```python
# In api_client.py, temporarily add:
server_sig = "FAKE_SIGNATURE_FOR_TESTING"
```

**Expected client output:**
```
[CLIENT] Verifying OVT signature for ovt_uuid=...
[CLIENT] ✗ Signature verification FAILED: ...
[CLIENT] ✗ SECURITY ALERT: OVT signature verification FAILED!
```

### Method 5: Test Blockchain Verification

1. Use admin panel `/blockchain/verify/<election_id>`
2. Tamper with a block using `/admin/simulate-tampering/<election_id>`
3. Verify again - should show signature failure

**Expected JSON response:**
```json
{
  "status": "tampered",
  "blocks": [
    {
      "index": 5,
      "signature_valid": false,
      "has_signature": true,
      "is_valid": false
    }
  ],
  "signature_failures": [
    {
      "block": 5,
      "error": "Signature verification failed"
    }
  ]
}
```

---

## ❌ Removed Fallback Code

### What Was Removed:

1. **Server-side crypto fallback** (lines 67-140 old version):
   ```python
   # OLD CODE - REMOVED:
   if CRYPTO_AVAILABLE:
       # Real RSA-PSS
   else:
       # INSECURE: base64(sha256(data)) fallback
       def sign_bytes_with_crypto(data_bytes):
           digest = hashlib.sha256(data_bytes).digest()
           return base64.b64encode(digest).decode()
   ```

2. **Client-side crypto fallback** (api_client.py):
   ```python
   # OLD CODE - REMOVED:
   try:
       from Crypto.Signature import pss
       CRYPTO_AVAILABLE = True
   except:
       CRYPTO_AVAILABLE = False
       
   # In verify_signature():
   if not CRYPTO_AVAILABLE:
       return True  # INSECURE: Skip verification
   ```

### Why Removed:

1. **Security:** Fallback signatures were not cryptographically secure (just SHA-256 hash)
2. **Academic Integrity:** Paper claims RSA-PSS signatures - must actually use them
3. **False Sense of Security:** System appeared to work but provided no real security
4. **Testing:** Fallback mode masked bugs in real crypto implementation

---

## 📝 Installation Requirements

To run BallotGuard, you MUST have:

```bash
pip install pycryptodome  # For RSA-PSS signatures (REQUIRED)
pip install face-recognition  # For real face auth (OPTIONAL - has fallback)
pip install dlib  # Required by face-recognition (OPTIONAL)
```

**Minimal Installation (for development):**
```bash
pip install pycryptodome numpy flask requests
```
- ✅ All crypto features work
- ⚠️ Face recognition uses NumPy fallback (acceptable for prototype)

**Full Installation (for production/paper):**
```bash
pip install -r requirements.txt
```
- ✅ All features with real algorithms
- ✅ Real CNN-based face recognition

---

## 🎯 Summary

| Feature | Library | Fallback? | Why |
|---------|---------|-----------|-----|
| OVT Signing | PyCryptodome (RSA-PSS) | ❌ NO | Critical security feature |
| Receipt Signing | PyCryptodome (RSA-PSS) | ❌ NO | Non-repudiation required |
| Block Signing | PyCryptodome (RSA-PSS) | ❌ NO | Blockchain integrity |
| Signature Verification | PyCryptodome (RSA-PSS) | ❌ NO | Security validation |
| Face Recognition | face_recognition + dlib | ✅ YES | Heavy dependency, NumPy works for prototype |

**Bottom Line:**
- **Crypto:** NO FALLBACK - System will crash if PyCryptodome missing
- **Face Recognition:** FALLBACK AVAILABLE - Uses NumPy if dlib not installed
- **All security-critical operations:** Logged to terminal with `[CRYPTO]`, `[AUTH]`, `[OVT]`, `[VOTE]`, `[RECEIPT]` prefixes

You can now monitor exactly what's happening by watching terminal output!
