from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "openai_configured" in body


def test_models_endpoint_hides_secrets():
    response = client.get("/api/models")
    assert response.status_code == 200
    payload = response.json()["models"]
    assert payload
    blob = str(payload).lower()
    assert "api_key" not in blob
    assert all("provider" in item and "model_id" in item for item in payload)
    providers = {item["provider"] for item in payload}
    assert "openai" in providers
    assert "groq" in providers


def test_execution_requires_installation_header():
    response = client.post(
        "/api/executions",
        json={
            "task": "hello",
            "model": {"provider": "openai", "model_id": "gpt-4o-mini"},
        },
    )
    assert response.status_code == 400


def test_execution_without_openai_key_is_rejected():
    from app.config import get_settings

    get_settings.cache_clear()
    if get_settings().openai_configured:
        return
    response = client.post(
        "/api/executions",
        headers={"X-Installation-Id": "test-install"},
        json={
            "task": "hello",
            "model": {"provider": "openai", "model_id": "gpt-4o-mini"},
        },
    )
    assert response.status_code == 400
    assert "OPENAI_API_KEY" in response.json()["detail"]
