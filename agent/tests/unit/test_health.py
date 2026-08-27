def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_healthy_status(client):
    response = client.get("/health")
    assert response.json() == {"status": "healthy"}


def test_health_rejects_post(client):
    response = client.post("/health")
    assert response.status_code == 405
