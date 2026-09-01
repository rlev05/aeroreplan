from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["service"] == "AeroReplan API"
    assert payload["status"] == "running"