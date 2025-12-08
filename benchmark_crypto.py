"""
BallotGuard Cryptographic Performance Benchmarking
Run this to get REAL timing data for your IEEE paper
"""

import time
import json
import numpy as np
from phe import paillier
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
import hashlib
import sys
import os

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, ROOT_DIR)

from server_backend.crypto import sha_utils
from client_app.crypto.paillier import paillier_encrypt

# Load real keys from your system
from server.server_config import PAILLIER_N, PAILLIER_P, PAILLIER_Q, RECEIPT_RSA_PRIV_PEM, RECEIPT_RSA_PUB_PEM

print("=" * 80)
print("BALLOTGUARD CRYPTOGRAPHIC PERFORMANCE BENCHMARK")
print("=" * 80)
print()

# Configuration
NUM_ITERATIONS = 50  # Reduced for faster testing
NUM_FACE_TESTS = 20  # Fewer for face recognition (slower)

results = {}

# ============================================================================
# 1. PAILLIER ENCRYPTION (Client-side)
# ============================================================================
print("📊 Testing Paillier Encryption...")
paillier_pubkey = paillier.PaillierPublicKey(PAILLIER_N)
paillier_privkey = paillier.PaillierPrivateKey(paillier_pubkey, PAILLIER_P, PAILLIER_Q)

encryption_times = []
for i in range(NUM_ITERATIONS):
    start = time.perf_counter()
    encrypted = paillier_encrypt(paillier_pubkey, 1)
    end = time.perf_counter()
    encryption_times.append((end - start) * 1000)  # Convert to ms

results['paillier_encryption'] = {
    'mean': np.mean(encryption_times),
    'std': np.std(encryption_times),
    'min': np.min(encryption_times),
    'max': np.max(encryption_times),
    'unit': 'ms',
    'iterations': NUM_ITERATIONS
}
print(f"   Mean: {results['paillier_encryption']['mean']:.2f} ± {results['paillier_encryption']['std']:.2f} ms")

# Pre-encrypt values for later use
encrypted_values = [paillier_encrypt(paillier_pubkey, 1) for _ in range(100)]

# ============================================================================
# 2. HOMOMORPHIC ADDITION (100 votes - smaller test)
# ============================================================================
print("📊 Testing Homomorphic Tallying (100 votes)...")
votes = [paillier_encrypt(paillier_pubkey, 1) for _ in range(100)]

start = time.perf_counter()
sum_encrypted = votes[0]
for vote in votes[1:]:
    sum_encrypted += vote
total = paillier_privkey.decrypt(sum_encrypted)
end = time.perf_counter()

results['homomorphic_tally_100'] = {
    'time': (end - start) * 1000,
    'unit': 'ms',
    'votes': 100,
    'result': total
}
print(f"   Total time: {results['homomorphic_tally_100']['time']:.2f} ms for 100 votes")
print(f"   Result: {total} votes (should be 100)")

# ============================================================================
# 4. RSA-PSS SIGNING (3072-bit - Receipts/OVT)
# ============================================================================
print("📊 Testing RSA-PSS Signing (3072-bit)...")
rsa_key = RSA.import_key(RECEIPT_RSA_PRIV_PEM)

signing_times = []
for i in range(NUM_ITERATIONS):
    data = json.dumps({"vote_id": f"V-{i}", "election_id": "EL-2025-01"}, sort_keys=True).encode()
    h = SHA256.new(data)
    
    start = time.perf_counter()
    signature = pss.new(rsa_key).sign(h)
    end = time.perf_counter()
    signing_times.append((end - start) * 1000)

results['rsa_pss_signing_3072'] = {
    'mean': np.mean(signing_times),
    'std': np.std(signing_times),
    'min': np.min(signing_times),
    'max': np.max(signing_times),
    'unit': 'ms',
    'iterations': NUM_ITERATIONS,
    'key_size': 3072
}
print(f"   Mean: {results['rsa_pss_signing_3072']['mean']:.2f} ± {results['rsa_pss_signing_3072']['std']:.2f} ms")

# ============================================================================
# 5. RSA-PSS VERIFICATION (3072-bit)
# ============================================================================
print("📊 Testing RSA-PSS Verification (3072-bit)...")
pub_key = RSA.import_key(RECEIPT_RSA_PUB_PEM)

# Generate signatures first
test_data = []
for i in range(NUM_ITERATIONS):
    data = json.dumps({"vote_id": f"V-{i}", "election_id": "EL-2025-01"}, sort_keys=True).encode()
    h = SHA256.new(data)
    sig = pss.new(rsa_key).sign(h)
    test_data.append((data, sig))

verification_times = []
for data, sig in test_data:
    h = SHA256.new(data)
    start = time.perf_counter()
    try:
        pss.new(pub_key).verify(h, sig)
        verified = True
    except:
        verified = False
    end = time.perf_counter()
    verification_times.append((end - start) * 1000)

results['rsa_pss_verification_3072'] = {
    'mean': np.mean(verification_times),
    'std': np.std(verification_times),
    'min': np.min(verification_times),
    'max': np.max(verification_times),
    'unit': 'ms',
    'iterations': NUM_ITERATIONS,
    'key_size': 3072
}
print(f"   Mean: {results['rsa_pss_verification_3072']['mean']:.2f} ± {results['rsa_pss_verification_3072']['std']:.2f} ms")

# ============================================================================
# 6. SHA-256 HASHING (Vote Hash)
# ============================================================================
print("📊 Testing SHA-256 Hashing...")
test_ciphertexts = [str(encrypted.ciphertext()) for encrypted in encrypted_values[:NUM_ITERATIONS]]

hashing_times = []
for ciphertext in test_ciphertexts:
    data = ciphertext + "election_salt_12345"
    start = time.perf_counter()
    hash_result = sha_utils.compute_sha256_hex(data)
    end = time.perf_counter()
    hashing_times.append((end - start) * 1000)

results['sha256_hashing'] = {
    'mean': np.mean(hashing_times),
    'std': np.std(hashing_times),
    'min': np.min(hashing_times),
    'max': np.max(hashing_times),
    'unit': 'ms',
    'iterations': NUM_ITERATIONS
}
print(f"   Mean: {results['sha256_hashing']['mean']:.2f} ± {results['sha256_hashing']['std']:.2f} ms")

# ============================================================================
# 6. BLOCKCHAIN HASH CHAIN VERIFICATION
# ============================================================================
print("📊 Testing Blockchain Hash Chain Verification...")
from server_backend.blockchain.blockchain import Block

# Create a chain of blocks
blockchain_verification_times = []
for i in range(50):  # Reduced from 500
    if i == 0:
        prev_hash = "GENESIS"
    else:
        prev_hash = f"hash_{i-1}"
    
    vote_hash = f"vote_hash_{i}"
    
    start = time.perf_counter()
    block = Block(i, time.time(), vote_hash, prev_hash)
    computed_hash = block.compute_hash()
    # Verify hash matches
    verified = (computed_hash == block.hash)
    end = time.perf_counter()
    
    blockchain_verification_times.append((end - start) * 1000)

results['blockchain_verification'] = {
    'mean': np.mean(blockchain_verification_times),
    'std': np.std(blockchain_verification_times),
    'min': np.min(blockchain_verification_times),
    'max': np.max(blockchain_verification_times),
    'unit': 'ms',
    'iterations': 50
}
print(f"   Mean: {results['blockchain_verification']['mean']:.2f} ± {results['blockchain_verification']['std']:.2f} ms")

# ============================================================================
# 7. FACE RECOGNITION (if available)
# ============================================================================
print("📊 Testing Face Recognition...")
try:
    import face_recognition
    import cv2
    
    # Generate dummy face encodings (128-D vectors)
    face_encoding_times = []
    distance_calculation_times = []
    
    # Simulate face encoding generation
    stored_encoding = np.random.rand(128)
    probe_encodings = [np.random.rand(128) for _ in range(NUM_FACE_TESTS)]
    
    # Distance calculation (what actually happens during verification)
    for probe in probe_encodings:
        start = time.perf_counter()
        distance = np.linalg.norm(stored_encoding - probe)
        match = (distance < 0.5)
        end = time.perf_counter()
        distance_calculation_times.append((end - start) * 1000)
    
    results['face_distance_calculation'] = {
        'mean': np.mean(distance_calculation_times),
        'std': np.std(distance_calculation_times),
        'min': np.min(distance_calculation_times),
        'max': np.max(distance_calculation_times),
        'unit': 'ms',
        'iterations': NUM_FACE_TESTS
    }
    print(f"   Distance calculation: {results['face_distance_calculation']['mean']:.4f} ± {results['face_distance_calculation']['std']:.4f} ms")
    print(f"   Note: Actual face encoding (CNN) takes ~300-500ms, not benchmarked here")
    
except ImportError:
    print("   ⚠️  face_recognition not available, skipping")
    results['face_distance_calculation'] = {'note': 'Not available'}

# ============================================================================
# CIPHERTEXT SIZE ANALYSIS
# ============================================================================
print("\n📊 Analyzing Ciphertext Sizes...")
sample_encrypted = paillier_encrypt(paillier_pubkey, 1)
ciphertext_str = str(sample_encrypted.ciphertext())
ciphertext_json = json.dumps({
    "ciphertext": ciphertext_str,
    "exponent": sample_encrypted.exponent
})

results['ciphertext_analysis'] = {
    'ciphertext_digits': len(ciphertext_str),
    'json_bytes': len(ciphertext_json.encode()),
    'public_key_bits': paillier_pubkey.n.bit_length(),
}
print(f"   Ciphertext length: {results['ciphertext_analysis']['ciphertext_digits']} digits")
print(f"   JSON size: {results['ciphertext_analysis']['json_bytes']} bytes")
print(f"   Public key: {results['ciphertext_analysis']['public_key_bits']} bits")

# ============================================================================
# PRINT SUMMARY TABLE
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY: CRYPTOGRAPHIC OPERATION PERFORMANCE")
print("=" * 80)
print(f"{'Operation':<35} | {'Algorithm':<15} | {'Mean (ms)':<12} | {'Std Dev (ms)':<12}")
print("-" * 80)

operations = [
    ("Paillier Encryption (Client)", "Paillier", "paillier_encryption"),
    ("RSA-PSS Signing (3072-bit)", "RSA-PSS", "rsa_pss_signing_3072"),
    ("RSA-PSS Verification (3072-bit)", "RSA-PSS", "rsa_pss_verification_3072"),
    ("SHA-256 Vote Hashing", "SHA-256", "sha256_hashing"),
    ("Blockchain Verification", "SHA-256", "blockchain_verification"),
]

if 'face_distance_calculation' in results and 'mean' in results['face_distance_calculation']:
    operations.append(("Face Distance Calculation", "Euclidean L2", "face_distance_calculation"))

for op_name, algorithm, key in operations:
    if key in results and 'mean' in results[key]:
        mean = results[key]['mean']
        std = results[key]['std']
        print(f"{op_name:<35} | {algorithm:<15} | {mean:>11.3f} | {std:>11.3f}")

print("-" * 80)
print(f"\nHomomorphic Tally (100 votes): {results['homomorphic_tally_100']['time']:.2f} ms")

# ============================================================================
# SAVE RESULTS TO JSON
# ============================================================================
output_file = "benchmark_results.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Results saved to: {output_file}")
print(f"\n🎯 Use these REAL values in your IEEE paper!")
print("=" * 80)
