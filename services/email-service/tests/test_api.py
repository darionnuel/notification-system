"""Test email API endpoints."""


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_email_health_check(client):
    """Test email API health check."""
    response = client.get("/api/v1/emails/health")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert response.json()["status"] == "running"
