from uuid import uuid4

from fastapi.testclient import TestClient


def _create_active_reservation(client: TestClient) -> tuple[int, int]:
    showtimes_response = client.get("/api/showtimes", params={"limit": 1, "offset": 0})
    assert showtimes_response.status_code == 200
    showtime_id = showtimes_response.json()["items"][0]["id"]

    seats_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    assert seats_response.status_code == 200
    seat = next(
        (item for item in seats_response.json()["seats"] if item["status"] == "AVAILABLE"),
        None,
    )
    assert seat is not None

    reservation_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [seat["seat_id"]]},
    )
    assert reservation_response.status_code == 201
    return reservation_response.json()["id"], showtime_id


def test_checkout_demo_confirm_marks_order_paid_and_sells_seat(client: TestClient) -> None:
    reservation_id, showtime_id = _create_active_reservation(client)

    checkout_response = client.post(
        "/api/checkout/session",
        json={"reservation_id": reservation_id},
    )
    assert checkout_response.status_code == 201
    checkout_payload = checkout_response.json()
    order_id = checkout_payload["order_id"]

    confirm_response = client.post("/api/checkout/demo/confirm", json={"order_id": order_id})
    assert confirm_response.status_code == 200
    confirm_payload = confirm_response.json()
    assert confirm_payload["order_status"] == "PAID"
    assert confirm_payload["ticket_count"] == 1

    seats_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    sold_count = len([seat for seat in seats_response.json()["seats"] if seat["status"] == "SOLD"])
    assert sold_count >= 1


def test_webhook_is_idempotent_for_duplicate_event_id(client: TestClient) -> None:
    reservation_id, _ = _create_active_reservation(client)

    checkout_response = client.post(
        "/api/checkout/session",
        json={"reservation_id": reservation_id},
    )
    assert checkout_response.status_code == 201
    provider_session_id = checkout_response.json()["provider_session_id"]

    event_id = f"evt_{uuid4().hex}"
    first_webhook = client.post(
        "/api/webhooks/stripe",
        headers={"x-webhook-secret": "change-me"},
        json={
            "event_id": event_id,
            "type": "checkout.session.completed",
            "data": {"provider_session_id": provider_session_id},
        },
    )
    assert first_webhook.status_code == 200
    assert first_webhook.json()["finalized"] is True

    second_webhook = client.post(
        "/api/webhooks/stripe",
        headers={"x-webhook-secret": "change-me"},
        json={
            "event_id": event_id,
            "type": "checkout.session.completed",
            "data": {"provider_session_id": provider_session_id},
        },
    )
    assert second_webhook.status_code == 200
    assert second_webhook.json()["duplicate"] is True
