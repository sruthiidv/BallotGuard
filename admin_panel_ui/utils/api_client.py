import requests

class APIClient:
    BASE_URL = "http://127.0.0.1:5000"
    def get_tally(self):
        try:
            r = requests.get(f"{self.BASE_URL}/admin/tally")
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def test_api(self):
        try:
            r = requests.get(f"{self.BASE_URL}/api/test")
            return r.json()
        except Exception as e:
            return {"error": str(e)}
