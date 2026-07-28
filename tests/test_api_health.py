from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Verify that the core API gateway is online and healthy."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "system" in response.json()

def test_vault_endpoint_unauthorized():
    """Verify that protected endpoints properly return 401 when unauthenticated."""
    response = client.post("/api/v1/vault/query", json={"query": "test", "workspace_id": 1, "top_k": 5})
    assert response.status_code == 401
