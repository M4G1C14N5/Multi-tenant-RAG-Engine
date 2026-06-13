from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_valid_tenant_starfolio():
    """Test with a valid tenant token."""
    response = client.get("/query?query=hello", headers={"Authorization": "Bearer starfolio"})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Querying vector database for: 'hello'",
        "secured_namespace": "starfolio"
    }

def test_valid_tenant_scouting_report():
    """Test with another valid tenant token."""
    response = client.get("/query?query=hello", headers={"Authorization": "Bearer scouting_report"})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Querying vector database for: 'hello'",
        "secured_namespace": "scouting_report"
    }

def test_invalid_tenant():
    """Test with an unauthorized/invalid tenant token."""
    response = client.get("/query?query=hello", headers={"Authorization": "Bearer hacker_namespace"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden: Invalid or unauthorized namespace requested."}

def test_missing_auth_header():
    """Test without an Authorization header."""
    response = client.get("/query?query=hello")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
