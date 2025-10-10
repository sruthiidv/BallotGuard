"""
Simple SHA-256 utilities for hashing strings/bytes.
"""

import hashlib

def compute_sha256_hex(data):
    """
    Return hex digest. Accepts str or bytes.
    """
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

def compute_sha256_bytes(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).digest()
