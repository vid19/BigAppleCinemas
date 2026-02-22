from fastapi.testclient import TestClient


def _first_available_seat(client: TestClient) -> tuple[int, int]:
    showtimes_response = client.get("/api/showtimes", params={"limit": 1, "offset": 0})
    assert showtimes_response.status_code == 200
    showtime_id = showtimes_response.json()["items"][0]["id"]

    seats_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    assert seats_response.status_code == 200
    available_seat = next(
        (seat for seat in seats_response.json()["seats"] if seat["status"] == "AVAILABLE"),
        None,
    )
    assert available_seat is not None
    return showtime_id, available_seat["seat_id"]


def test_create_get_and_delete_reservation(client: TestClient) -> None:
    showtime_id, seat_id = _first_available_seat(client)

    create_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [seat_id]},
    )
    assert create_response.status_code == 201
    reservation_payload = create_response.json()
    reservation_id = reservation_payload["id"]

    assert reservation_payload["status"] == "ACTIVE"
    assert reservation_payload["seat_ids"] == [seat_id]

    get_response = client.get(f"/api/reservations/{reservation_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "ACTIVE"

    seat_map_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    seat_payload = seat_map_response.json()
    held_seat = next(seat for seat in seat_payload["seats"] if seat["seat_id"] == seat_id)
    assert held_seat["status"] == "HELD"

    delete_response = client.delete(f"/api/reservations/{reservation_id}")
    assert delete_response.status_code == 204

    refreshed_seat_map_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    refreshed_payload = refreshed_seat_map_response.json()
    released_seat = next(seat for seat in refreshed_payload["seats"] if seat["seat_id"] == seat_id)
    assert released_seat["status"] == "AVAILABLE"


def test_reservation_blocks_double_hold(client: TestClient) -> None:
    showtime_id, seat_id = _first_available_seat(client)

    first_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [seat_id]},
    )
    assert first_response.status_code == 201
    reservation_id = first_response.json()["id"]

    second_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [seat_id]},
    )
    assert second_response.status_code == 409

    cleanup_response = client.delete(f"/api/reservations/{reservation_id}")
    assert cleanup_response.status_code == 204


def test_active_reservation_endpoint_returns_current_hold(client: TestClient) -> None:
    showtime_id, seat_id = _first_available_seat(client)

    empty_response = client.get("/api/reservations/active", params={"showtime_id": showtime_id})
    assert empty_response.status_code == 200
    assert empty_response.json() is None

    create_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [seat_id]},
    )
    assert create_response.status_code == 201
    reservation_id = create_response.json()["id"]

    active_response = client.get("/api/reservations/active", params={"showtime_id": showtime_id})
    assert active_response.status_code == 200
    payload = active_response.json()
    assert payload["id"] == reservation_id
    assert payload["status"] == "ACTIVE"
    assert payload["seat_ids"] == [seat_id]

    cleanup_response = client.delete(f"/api/reservations/{reservation_id}")
    assert cleanup_response.status_code == 204
