import requests
import json
import time

class APIClient:
    BASE_URL = "http://127.0.0.1:5000"
    
    def __init__(self):
        self.mock_data = {
            'total_votes': 157,
            'status': 'success',
            'candidates': [
                {'name': 'Candidate A', 'votes': 89},
                {'name': 'Candidate B', 'votes': 68},
            ],
            'system_health': 'Online',
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_tally(self):
        try:
            r = requests.get(f"{self.BASE_URL}/admin/tally", timeout=2)
            return r.json()
        except Exception as e:
            print(f"API offline, using mock data: {e}")
            # Return mock data for demonstration
            return {
                "total_votes": self.mock_data['total_votes'],
                "status": "success (demo mode)",
                "message": "Demo mode - Flask server offline"
            }
    
    def test_api(self):
        try:
            r = requests.get(f"{self.BASE_URL}/api/test", timeout=2)
            return r.json()
        except Exception as e:
            return {
                "status": "offline",
                "message": "Flask server not running - using demo mode"
            }
    
    def get_system_health(self):
        try:
            r = requests.get(f"{self.BASE_URL}/admin/health", timeout=2)
            return r.json()
        except Exception as e:
            return {
                "status": "Demo Mode",
                "server": "Offline", 
                "ui_status": "Working"
            }
    
    def get_detailed_tally(self):
        try:
            # Try real API first
            r = requests.get(f"{self.BASE_URL}/admin/tally", timeout=2)
            return r.json()
        except Exception:
            # Return detailed mock data
            return {
                "total_votes": self.mock_data['total_votes'],
                "candidates": self.mock_data['candidates'],
                "status": "success",
                "timestamp": self.mock_data['last_updated'],
                "mode": "demo"
            }
