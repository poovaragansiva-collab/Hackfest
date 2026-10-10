"""Automated tests for CORS configuration and preflight handling.

Verifies:
1. Preflight OPTIONS requests for /api/v1/infer-purpose and /api/v1/generate from allowed origins (http://127.0.0.1:5173 and http://localhost:5173).
2. Proper Access-Control-Allow-Origin, Access-Control-Allow-Methods, and Access-Control-Allow-Headers.
3. Access-Control-Allow-Credentials is true while Access-Control-Allow-Origin is never a wildcard '*'.
4. Rejection of untrusted / non-loopback origins (e.g. http://malicious-site.com).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.mark.parametrize("origin", [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
])
def test_cors_preflight_infer_purpose_allowed(origin: str):
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/api/v1/infer-purpose", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.parametrize("origin", [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
])
def test_cors_preflight_generate_allowed(origin: str):
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type, authorization",
    }
    response = client.options("/api/v1/generate", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_post_infer_purpose_allowed_origin():
    headers = {
        "Origin": "http://127.0.0.1:5173",
        "Content-Type": "application/json",
    }
    response = client.post(
        "/api/v1/infer-purpose",
        json={"prompt": "A coloring sheet of a lion for kindergarten"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_rejected_untrusted_origin():
    headers = {
        "Origin": "https://malicious-external-site.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/api/v1/generate", headers=headers)
    # CORSMiddleware returns 400 Disallowed CORS origin for disallowed origins
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
