from fastapi.testclient import TestClient
from pydantic import SecretStr
from questiontrail.main import app
from questiontrail.settings import Settings, get_settings


def test_health_endpoint_default():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "QuestionTrail API"
    assert data["llm_provider"] == "auto"
    assert isinstance(data["fallback_order"], list)
    assert data["has_nvidia_key"] is False
    assert data["has_gemini_key"] is False
    
    # Verify no secret keys or values are emitted in the response
    for key, value in data.items():
        assert "key" not in key.lower() or key in ("has_nvidia_key", "has_gemini_key")
        assert not isinstance(value, str) or "nvapi-" not in value


def test_health_endpoint_with_secrets_does_not_leak():
    # Inject fake settings with actual secret values
    fake_settings = Settings(
        nvidia_api_key=SecretStr("nvapi-super-confidential-secret-key"),
        gemini_api_key=SecretStr("gemini-super-confidential-key"),
        llm_provider="nvidia"
    )
    
    app.dependency_overrides[get_settings] = lambda: fake_settings
    try:
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["llm_provider"] == "nvidia"
        assert data["has_nvidia_key"] is True
        assert data["has_gemini_key"] is True
        
        # Verify strict absence of the secret strings in raw response text
        raw_text = response.text
        assert "nvapi-super-confidential-secret-key" not in raw_text
        assert "gemini-super-confidential-key" not in raw_text
    finally:
        app.dependency_overrides.clear()
