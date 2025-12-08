"""
Generate self-signed SSL certificates for HTTPS server
Run this script to enable TLS/HTTPS on the BallotGuard server
"""

import os
import subprocess
import sys

def generate_certificates():
    # Create certs directory
    certs_dir = os.path.join(os.path.dirname(__file__), 'certs')
    os.makedirs(certs_dir, exist_ok=True)
    
    cert_file = os.path.join(certs_dir, 'server.crt')
    key_file = os.path.join(certs_dir, 'server.key')
    
    # Check if certificates already exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✓ SSL certificates already exist:")
        print(f"  Certificate: {cert_file}")
        print(f"  Private Key: {key_file}")
        
        overwrite = input("\nOverwrite existing certificates? (y/N): ").lower()
        if overwrite != 'y':
            print("Keeping existing certificates.")
            return
    
    print("\n🔐 Generating self-signed SSL certificate...")
    print("This certificate is suitable for development/testing only.")
    print("\nYou'll be prompted for certificate information.")
    print("You can press ENTER to accept defaults for most fields.\n")
    
    # Generate self-signed certificate using openssl
    cmd = [
        'openssl', 'req', '-x509',
        '-newkey', 'rsa:4096',
        '-nodes',
        '-out', cert_file,
        '-keyout', key_file,
        '-days', '365',
        '-subj', '/CN=localhost/O=BallotGuard/C=IN'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ SSL certificates generated successfully!")
        print(f"\n📁 Certificate files:")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        print(f"\n🔒 Valid for: 365 days")
        print(f"\n⚠️  Note: This is a self-signed certificate.")
        print("   Browsers will show a security warning.")
        print("   For production, use a certificate from a trusted CA.\n")
        
        print("✓ Server will now run with HTTPS enabled.")
        print("  Access at: https://127.0.0.1:8443")
        
    except FileNotFoundError:
        print("\n❌ ERROR: OpenSSL not found!")
        print("\nPlease install OpenSSL:")
        print("  Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("  Linux:   sudo apt-get install openssl")
        print("  macOS:   brew install openssl")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: Failed to generate certificates: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("="*60)
    print("  BallotGuard - SSL Certificate Generator")
    print("="*60)
    generate_certificates()
