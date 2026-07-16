import requests
from app.auth.jwt_handler import create_access_token

token = create_access_token({"user_id": 1, "username": "test", "department": "PROCUREMENT"})
headers = {"Authorization": f"Bearer {token}"}

print("Hitting /conversations...")
try:
    res = requests.get("http://127.0.0.1:8000/conversations", headers=headers, timeout=15)
    print(res.status_code)
    print(res.text)
except Exception as e:
    print("Error:", e)
