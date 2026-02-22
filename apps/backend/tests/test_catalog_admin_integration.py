from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


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


def test_showtime_seat_map_endpoint_returns_inventory(client: TestClient) -> None:
    showtimes_response = client.get("/api/showtimes", params={"limit": 1, "offset": 0})
    assert showtimes_response.status_code == 200
    showtime_id = showtimes_response.json()["items"][0]["id"]

    seats_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    assert seats_response.status_code == 200

    payload = seats_response.json()
    assert payload["showtime_id"] == showtime_id
    assert len(payload["seats"]) > 0
    assert all("status" in seat for seat in payload["seats"])


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


def test_showtimes_hide_past_by_default(client: TestClient) -> None:
    create_movie_response = client.post(
        "/api/admin/movies",
        json={
            "title": "Showtime Filter Movie",
            "description": "Movie used for showtime filtering integration test",
            "runtime_minutes": 105,
            "rating": "PG-13",
        },
    )
    assert create_movie_response.status_code == 201
    movie_id = create_movie_response.json()["id"]

    now = datetime.now(tz=UTC).replace(microsecond=0)
    past_starts_at = now - timedelta(hours=5)
    future_starts_at = now + timedelta(hours=5)

    past_response = client.post(
        "/api/admin/showtimes",
        json={
            "movie_id": movie_id,
            "auditorium_id": 1,
            "starts_at": past_starts_at.isoformat(),
            "ends_at": (past_starts_at + timedelta(hours=2)).isoformat(),
            "status": "SCHEDULED",
        },
    )
    assert past_response.status_code == 201
    past_showtime_id = past_response.json()["id"]

    future_response = client.post(
        "/api/admin/showtimes",
        json={
            "movie_id": movie_id,
            "auditorium_id": 1,
            "starts_at": future_starts_at.isoformat(),
            "ends_at": (future_starts_at + timedelta(hours=2)).isoformat(),
            "status": "SCHEDULED",
        },
    )
    assert future_response.status_code == 201
    future_showtime_id = future_response.json()["id"]

    default_list = client.get(
        "/api/showtimes",
        params={"movie_id": movie_id, "limit": 20, "offset": 0},
    )
    assert default_list.status_code == 200
    default_ids = {item["id"] for item in default_list.json()["items"]}
    assert future_showtime_id in default_ids
    assert past_showtime_id not in default_ids

    include_past_list = client.get(
        "/api/showtimes",
        params={"movie_id": movie_id, "include_past": "true", "limit": 20, "offset": 0},
    )
    assert include_past_list.status_code == 200
    include_past_ids = {item["id"] for item in include_past_list.json()["items"]}
    assert future_showtime_id in include_past_ids
    assert past_showtime_id in include_past_ids

    assert client.delete(f"/api/admin/showtimes/{past_showtime_id}").status_code == 204
    assert client.delete(f"/api/admin/showtimes/{future_showtime_id}").status_code == 204
    assert client.delete(f"/api/admin/movies/{movie_id}").status_code == 204


def test_movie_delete_cascades_unbooked_showtimes(client: TestClient) -> None:
    create_movie_response = client.post(
        "/api/admin/movies",
        json={
            "title": "Delete Cascade Movie",
            "description": "Movie used to validate cascade delete behavior",
            "runtime_minutes": 100,
            "rating": "PG-13",
        },
    )
    assert create_movie_response.status_code == 201
    movie_id = create_movie_response.json()["id"]

    starts_at = datetime.now(tz=UTC).replace(microsecond=0) + timedelta(hours=10)
    ends_at = starts_at + timedelta(hours=2)
    create_showtime_response = client.post(
        "/api/admin/showtimes",
        json={
            "movie_id": movie_id,
            "auditorium_id": 1,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "status": "SCHEDULED",
        },
    )
    assert create_showtime_response.status_code == 201

    delete_response = client.delete(f"/api/admin/movies/{movie_id}")
    assert delete_response.status_code == 204

    showtime_list_response = client.get(
        "/api/showtimes",
        params={"movie_id": movie_id, "include_past": "true", "limit": 10, "offset": 0},
    )
    assert showtime_list_response.status_code == 200
    assert showtime_list_response.json()["total"] == 0


def test_movie_delete_rejected_when_orders_exist(client: TestClient) -> None:
    create_movie_response = client.post(
        "/api/admin/movies",
        json={
            "title": "Delete Blocked Movie",
            "description": "Movie used to validate order-protected delete behavior",
            "runtime_minutes": 108,
            "rating": "PG-13",
        },
    )
    assert create_movie_response.status_code == 201
    movie_id = create_movie_response.json()["id"]

    starts_at = datetime.now(tz=UTC).replace(microsecond=0) + timedelta(hours=11)
    ends_at = starts_at + timedelta(hours=2)
    create_showtime_response = client.post(
        "/api/admin/showtimes",
        json={
            "movie_id": movie_id,
            "auditorium_id": 1,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "status": "SCHEDULED",
        },
    )
    assert create_showtime_response.status_code == 201
    showtime_id = create_showtime_response.json()["id"]

    seats_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    assert seats_response.status_code == 200
    available_seat = next(
        (seat for seat in seats_response.json()["seats"] if seat["status"] == "AVAILABLE"),
        None,
    )
    assert available_seat is not None

    reservation_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [available_seat["seat_id"]]},
    )
    assert reservation_response.status_code == 201
    reservation_id = reservation_response.json()["id"]

    checkout_response = client.post(
        "/api/checkout/session",
        json={"reservation_id": reservation_id},
    )
    assert checkout_response.status_code == 201
    order_id = checkout_response.json()["order_id"]

    confirm_response = client.post(
        "/api/checkout/demo/confirm",
        json={"order_id": order_id},
    )
    assert confirm_response.status_code == 200

    delete_response = client.delete(f"/api/admin/movies/{movie_id}")
    assert delete_response.status_code == 409
    assert "tickets/orders exist" in delete_response.json()["detail"]
