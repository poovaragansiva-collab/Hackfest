import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_validation_missing_prompt():
    response = client.post(
        "/api/v1/generate",
        json={"intended_use": "coloring_worksheet"},
    )
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any(err["loc"][-1] == "prompt" for err in errors)


def test_validation_prompt_too_short():
    response = client.post(
        "/api/v1/generate",
        json={"prompt": "hi", "intended_use": "coloring_worksheet"},
    )
    assert response.status_code == 422


def test_validation_invalid_intended_use():
    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "An outline of a cat",
            "intended_use": "invalid_unknown_purpose",
        },
    )
    assert response.status_code == 422
