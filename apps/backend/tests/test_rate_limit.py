from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings

DEMO_ADMIN_EMAIL = "demo@bigapplecinemas.local"
DEMO_ADMIN_PASSWORD = "DemoAdmin123!"


def test_auth_login_rate_limit_enforced(client: TestClient) -> None:
    forwarded_ip = f"10.{uuid4().int % 255}.{uuid4().int % 255}.{uuid4().int % 255}"
    previous_limit = settings.rate_limit_auth_login
    previous_window = settings.rate_limit_auth_window_seconds
    original_auth_header = client.headers.get("Authorization")
    settings.rate_limit_auth_login = 2
    settings.rate_limit_auth_window_seconds = 60

    try:
        client.headers.pop("Authorization", None)
        headers = {"x-forwarded-for": forwarded_ip}
        payload = {"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD}
        first_response = client.post("/api/auth/login", json=payload, headers=headers)
        second_response = client.post("/api/auth/login", json=payload, headers=headers)
        third_response = client.post("/api/auth/login", json=payload, headers=headers)
    finally:
        if original_auth_header:
            client.headers.update({"Authorization": original_auth_header})
        settings.rate_limit_auth_login = previous_limit
        settings.rate_limit_auth_window_seconds = previous_window

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert third_response.status_code == 429
