import pytest
from fastapi.testclient import TestClient

from app.main import app

DEMO_ADMIN_EMAIL = "demo@bigapplecinemas.local"
DEMO_ADMIN_PASSWORD = "DemoAdmin123!"


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        login_response = test_client.post(
            "/api/auth/login",
            json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client
