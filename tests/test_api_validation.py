import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_validation_error():
    # Send an invalid payload (missing password, short username)
    response = client.post("/register", json={
        "username": "a", # Too short
        "email": "invalid-email" # Invalid email
    })
    
    assert response.status_code == 422
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    
    fields_with_errors = [detail["field"] for detail in data["error"]["details"]]
    assert "body.username" in fields_with_errors
    assert "body.email" in fields_with_errors
    assert "body.password" in fields_with_errors

def test_login_validation_error():
    response = client.post("/login", json={
        "username": "", # Too short
        # missing password
    })
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["error"]["code"] == "VALIDATION_ERROR"
    fields = [d["field"] for d in data["error"]["details"]]
    assert "body.username" in fields
    assert "body.password" in fields

def test_complete_auth_and_upload_flow():
    import uuid
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    
    # 1. Register User
    reg_resp = client.post("/register", json={
        "username": username,
        "email": email,
        "password": "strongpassword123",
        "department": "FINANCE"
    })
    assert reg_resp.status_code == 200
    
    # 2. Login User
    login_resp = client.post("/login", json={
        "username": username,
        "password": "strongpassword123"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["department"] == "FINANCE"
    
    # 3. Refresh Token
    refresh_resp = client.post("/refresh", json={
        "refresh_token": login_data["refresh_token"]
    })
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    
    # 4. Upload Invalid File
    headers = {"Authorization": f"Bearer {refresh_data['access_token']}"}
    files = {"file": ("malicious.sh", b"rm -rf /", "text/plain")}
    upload_resp = client.post("/upload", files=files, headers=headers)
    assert upload_resp.status_code == 400
    assert "Only PDF and image uploads are supported" in upload_resp.json()["detail"]
