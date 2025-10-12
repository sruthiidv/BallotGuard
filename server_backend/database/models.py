# Simplified models.py - Database setup is Person 2's responsibility
# This file exists to prevent import errors until Person 2 completes database setup

# TODO: Person 2 will implement proper database models here
# For now, we'll use mock models to prevent import errors

class MockDB:
    """Mock database class until Person 2 sets up real database"""
    def init_app(self, app):
        pass

db = MockDB()

# Mock model classes (Person 2 will replace these with real SQLAlchemy models)
class Voter:
    pass

class Vote:
    pass

class BlockchainRecord:
    pass
