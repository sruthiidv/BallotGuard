from setuptools import setup, find_packages

setup(
    name="client_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'customtkinter>=5.1.3',
        'requests>=2.31.0',
        'opencv-python>=4.8.0',
        'pynacl>=1.5.0',        # For Ed25519 signing
        'pycryptodome>=3.19.0', # For cryptographic operations
        'phe>=1.5.0'            # For Paillier homomorphic encryption
    ]
)
#.venv\Scripts\activate