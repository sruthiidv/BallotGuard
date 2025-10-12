import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ballotguard-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost/ballotguard_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
