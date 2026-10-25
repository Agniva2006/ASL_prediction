"""
Integration tests for Sign0 REST API endpoints.
"""


def test_root_endpoint(test_client):
    """Verify root status endpoint returns 200 OK."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "service" in data


def test_health_ready_endpoint(test_client):
    """Verify readiness check endpoint."""
    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "database_connected" in data


def test_prometheus_metrics_endpoint(test_client):
    """Verify Prometheus metrics exposition endpoint returns text/plain."""
    response = test_client.get("/metrics")
    assert response.status_code == 200
    assert "sign0_inference_requests_total" in response.text


def test_predict_mlp_endpoint(test_client, sample_landmarks_63):
    """Verify /api/v1/predict endpoint."""
    payload = {"landmarks": sample_landmarks_63}
    response = test_client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data


def test_synthesis_dictionary_endpoint(test_client):
    """Verify dictionary retrieval endpoint."""
    response = test_client.get("/api/v1/synthesis/dictionary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_plans_endpoint(test_client):
    """Verify plans endpoint."""
    response = test_client.get("/auth/plans")
    assert response.status_code == 200
    data = response.json()
    assert "free" in data
    assert "pro" in data
