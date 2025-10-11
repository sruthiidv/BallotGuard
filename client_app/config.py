SERVER_BASE = "http://127.0.0.1:8443"   # local HTTP (no TLS)
BOOTH_ID = "B-01"

# ---- Paillier public key (paste from server) ----
# Use decimal integers; g is typically n+1 (ignored by phe).
PAILLIER_N = int("10031678375303998253006513457668115548517661809089908476411202876298497600988778037540092669856512628938099894577222100820907476625432023551889039106945181")  # TODO: put real n here
PAILLIER_G = int("0")  # optional; phe uses n+1 internally

# ---- OVT (Ed25519) server public key (base64, 32 bytes) ----
SERVER_SIGN_PUBKEY_B64 = "SW2b8GnGUl1HQjwVgBGF/mi0YxqIkhWmPpslcrkom+E="  # TODO

# ---- Receipt RSA public key (PEM) for RSA-PSS verification) ----
RECEIPT_RSA_PUB_PEM = """-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyiABI7/cL1S6HcP+hiIg\nHvIhxEDnxsNPiSxNHdqSKgyVJdjgHOtjZaULLVrANJfvGRIlcHQiQ1WRyggGw5O7\nYwwXnKQ1ZDk3HPpGMDNEHwljSao2AZwfugsmuI2w/gRBMx+cdi/seTQKQcsCHyFj\nPj8X8kd/eaLxS5IM+07x6tDF1OBwVUuGJntiGsc/X0floRq037fImupbXswHr7ey\nHEjUO679i+Np6c2IShkJswpczasGJOavSnKStnGJ+M/jqiqmg5HJsvQ0Amz9Tbfz\n27v6cKNO4n2IoVceYl86unDTnblwP2omYRsSb6eKUeT67NbWne/ETcOTe1+G3bSD\nBQIDAQAB\n-----END PUBLIC KEY-----"""

# Camera index for OpenCV (0 = default cam)
CAM_INDEX = 0

# UI polling + HTTP timeouts
OPEN_ELECTION_POLL_SECS = 5
HTTP_TIMEOUT = 10
