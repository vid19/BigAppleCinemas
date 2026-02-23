from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings


def test_register_login_and_me_flow(client: TestClient) -> None:
    email = f"user-{uuid4().hex[:10]}@bigapplecinemas.local"
    password = "Password123!"

    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["user"]["email"] == email
    assert register_payload["refresh_token"]
    assert register_payload["access_expires_in_seconds"] > 0
    assert register_payload["refresh_expires_in_seconds"] > 0

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    token = login_payload["access_token"]
    refresh_token = login_payload["refresh_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["access_token"]
    assert refreshed_payload["refresh_token"] != refresh_token
    stale_refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert stale_refresh_response.status_code == 401

    logout_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {refreshed_payload['access_token']}"},
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert logout_response.status_code == 204


def test_auth_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_auth_limits_active_refresh_sessions(client: TestClient) -> None:
    original_max_sessions = settings.auth_max_active_sessions
    settings.auth_max_active_sessions = 2
    try:
        email = f"sessions-{uuid4().hex[:10]}@bigapplecinemas.local"
        password = "Password123!"

        register_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password},
        )
        assert register_response.status_code == 201
        oldest_refresh_token = register_response.json()["refresh_token"]

        first_login = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert first_login.status_code == 200

        second_login = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert second_login.status_code == 200

        stale_refresh_attempt = client.post(
            "/api/auth/refresh",
            json={"refresh_token": oldest_refresh_token},
        )
        assert stale_refresh_attempt.status_code == 401
    finally:
        settings.auth_max_active_sessions = original_max_sessions
