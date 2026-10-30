from fastapi.testclient import TestClient

from pathlib import Path

from app.main import app, configured_model_path


client = TestClient(app)


def test_prediction_requires_internal_api_key(monkeypatch):
    monkeypatch.setenv("MONITORING_API_KEY", "test-internal-key")

    response = client.post("/api/v1/ai/predict", json={"features": {}})

    assert response.status_code == 401


def test_valid_key_reaches_request_validation(monkeypatch):
    monkeypatch.setenv("MONITORING_API_KEY", "test-internal-key")

    response = client.post(
        "/api/v1/ai/predict",
        headers={"X-Internal-API-Key": "test-internal-key"},
        json={},
    )

    assert response.status_code == 422


def test_prometheus_metrics_are_available_without_sensitive_values():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "ai_security_requests_total" in response.text
    assert "MONITORING_API_KEY" not in response.text


def test_configured_model_path_does_not_evaluate_repository_fallback(monkeypatch):
    container_path = "/models/model.joblib"
    monkeypatch.setenv("AI_MODEL_PATH", container_path)

    assert configured_model_path() == Path(container_path)
