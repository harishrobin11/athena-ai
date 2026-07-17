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
