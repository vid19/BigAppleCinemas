from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings


def test_auth_login_rate_limit_enforced(client: TestClient) -> None:
    unique_user_id = str((uuid4().int % 1_000_000_000) + 1)
    previous_limit = settings.rate_limit_auth_login
    previous_window = settings.rate_limit_auth_window_seconds
    settings.rate_limit_auth_login = 2
    settings.rate_limit_auth_window_seconds = 60

    try:
        first_response = client.post("/api/auth/login", headers={"x-user-id": unique_user_id})
        second_response = client.post("/api/auth/login", headers={"x-user-id": unique_user_id})
        third_response = client.post("/api/auth/login", headers={"x-user-id": unique_user_id})
    finally:
        settings.rate_limit_auth_login = previous_limit
        settings.rate_limit_auth_window_seconds = previous_window

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert third_response.status_code == 429
