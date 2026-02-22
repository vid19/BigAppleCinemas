from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_catalog_list_endpoints_return_seeded_data(client: TestClient) -> None:
    movies_response = client.get("/api/movies", params={"limit": 5, "offset": 0})
    theaters_response = client.get("/api/theaters", params={"limit": 5, "offset": 0})
    showtimes_response = client.get("/api/showtimes", params={"limit": 5, "offset": 0})

    assert movies_response.status_code == 200
    assert theaters_response.status_code == 200
    assert showtimes_response.status_code == 200

    movies_payload = movies_response.json()
    theaters_payload = theaters_response.json()
    showtimes_payload = showtimes_response.json()

    assert movies_payload["total"] >= 1
    assert theaters_payload["total"] >= 1
    assert showtimes_payload["total"] >= 1


def test_admin_movie_crud_flow(client: TestClient) -> None:
    create_response = client.post(
        "/api/admin/movies",
        json={
            "title": "Integration Movie",
            "description": "Created by integration test",
            "runtime_minutes": 99,
            "rating": "PG",
            "metadata_json": {"genre": ["Drama"]},
        },
    )
    assert create_response.status_code == 201
    movie_id = create_response.json()["id"]

    patch_response = client.patch(f"/api/admin/movies/{movie_id}", json={"rating": "PG-13"})
    assert patch_response.status_code == 200
    assert patch_response.json()["rating"] == "PG-13"

    delete_response = client.delete(f"/api/admin/movies/{movie_id}")
    assert delete_response.status_code == 204


def test_admin_showtime_crud_flow(client: TestClient) -> None:
    movies_response = client.get("/api/movies", params={"limit": 1, "offset": 0})
    movie_id = movies_response.json()["items"][0]["id"]

    starts_at = datetime.now(tz=UTC).replace(microsecond=0) + timedelta(hours=12)
    ends_at = starts_at + timedelta(hours=2)

    create_response = client.post(
        "/api/admin/showtimes",
        json={
            "movie_id": movie_id,
            "auditorium_id": 1,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "status": "SCHEDULED",
        },
    )
    assert create_response.status_code == 201
    showtime_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/admin/showtimes/{showtime_id}",
        json={"status": "CANCELED"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "CANCELED"

    delete_response = client.delete(f"/api/admin/showtimes/{showtime_id}")
    assert delete_response.status_code == 204
