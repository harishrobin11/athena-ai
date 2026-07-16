from fastapi.testclient import TestClient
from app.main import app
import traceback
try:
    client = TestClient(app)
    response = client.post("/login", json={"username": "admin", "password": "password"})
    print("Response status:", response.status_code)
    print("Response body:", response.text)
except Exception as e:
    traceback.print_exc()
