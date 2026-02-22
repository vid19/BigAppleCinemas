from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def _register_user_headers(client: TestClient) -> dict[str, str]:
    email = f"reco-{uuid4().hex[:10]}@bigapplecinemas.local"
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_paid_ticket(
    client: TestClient,
    *,
    headers: dict[str, str] | None = None,
) -> dict[str, int | str]:
    showtimes_response = client.get("/api/showtimes", params={"limit": 1, "offset": 0})
    assert showtimes_response.status_code == 200
    showtime_id = showtimes_response.json()["items"][0]["id"]

    seats_response = client.get(f"/api/showtimes/{showtime_id}/seats")
    seat = next(
        (item for item in seats_response.json()["seats"] if item["status"] == "AVAILABLE"),
        None,
    )
    assert seat is not None

    reservation_response = client.post(
        "/api/reservations",
        json={"showtime_id": showtime_id, "seat_ids": [seat["seat_id"]]},
        headers=headers,
    )
    assert reservation_response.status_code == 201
    reservation_id = reservation_response.json()["id"]

    checkout_response = client.post(
        "/api/checkout/session",
        json={"reservation_id": reservation_id},
        headers=headers,
    )
    assert checkout_response.status_code == 201
    order_id = checkout_response.json()["order_id"]

    confirm_response = client.post(
        "/api/checkout/demo/confirm",
        json={"order_id": order_id},
        headers=headers,
    )
    assert confirm_response.status_code == 200
    tickets = confirm_response.json()["tickets"]
    assert len(tickets) == 1
    return {"qr_token": tickets[0]["qr_token"], "showtime_id": showtime_id}


def test_ticket_scan_valid_then_already_used(client: TestClient) -> None:
    ticket = _create_paid_ticket(client)
    qr_token = str(ticket["qr_token"])

    first_scan = client.post(
        "/api/tickets/scan",
        headers={"x-staff-token": "local-staff"},
        json={"qr_token": qr_token},
    )
    assert first_scan.status_code == 200
    assert first_scan.json()["result"] == "VALID"

    second_scan = client.post(
        "/api/tickets/scan",
        headers={"x-staff-token": "local-staff"},
        json={"qr_token": qr_token},
    )
    assert second_scan.status_code == 200
    assert second_scan.json()["result"] == "ALREADY_USED"


def test_ticket_scan_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/api/tickets/scan",
        headers={"x-staff-token": "local-staff"},
        json={"qr_token": "invalid-token"},
    )
    assert response.status_code == 200
    assert response.json()["result"] == "INVALID"


def test_ticket_scan_rejects_expired_showtime(client: TestClient) -> None:
    ticket = _create_paid_ticket(client)
    qr_token = str(ticket["qr_token"])
    showtime_id = int(ticket["showtime_id"])
    now = datetime.now(tz=UTC)

    patch_response = client.patch(
        f"/api/admin/showtimes/{showtime_id}",
        json={
            "starts_at": (now - timedelta(hours=3)).isoformat(),
            "ends_at": (now - timedelta(minutes=25)).isoformat(),
        },
    )
    assert patch_response.status_code == 200

    scan_response = client.post(
        "/api/tickets/scan",
        headers={"x-staff-token": "local-staff"},
        json={"qr_token": qr_token},
    )
    assert scan_response.status_code == 200
    assert scan_response.json()["result"] == "INVALID"
    assert "expired" in scan_response.json()["message"].lower()


def test_me_endpoints_return_orders_and_tickets(client: TestClient) -> None:
    _create_paid_ticket(client)

    tickets_response = client.get("/api/me/tickets")
    orders_response = client.get("/api/me/orders")

    assert tickets_response.status_code == 200
    assert orders_response.status_code == 200
    assert tickets_response.json()["total"] >= 1
    assert orders_response.json()["total"] >= 1


def test_me_recommendations_endpoint_returns_ranked_movies(client: TestClient) -> None:
    headers = _register_user_headers(client)
    _create_paid_ticket(client, headers=headers)

    tickets_response = client.get("/api/me/tickets", headers=headers)
    assert tickets_response.status_code == 200
    watched_movies = {item["movie_title"] for item in tickets_response.json()["items"]}

    response = client.get("/api/me/recommendations", params={"limit": 5}, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1
    first_item = payload["items"][0]
    assert "movie_id" in first_item
    assert "reason" in first_item
    assert isinstance(first_item["score"], float)
    assert first_item["title"] not in watched_movies
    assert any(
        item["reason"].startswith("Because you watched") or item["reason"].startswith("Trending")
        for item in payload["items"]
    )


def test_recommendation_feedback_filters_not_interested_movies(client: TestClient) -> None:
    headers = _register_user_headers(client)

    recommendations = client.get("/api/me/recommendations", params={"limit": 10}, headers=headers)
    assert recommendations.status_code == 200
    items = recommendations.json()["items"]
    assert items

    movie_id = items[0]["movie_id"]
    feedback_response = client.post(
        "/api/me/recommendations/feedback",
        json={
            "movie_id": movie_id,
            "event_type": "NOT_INTERESTED",
            "active": True,
        },
        headers=headers,
    )
    assert feedback_response.status_code == 200
    assert feedback_response.json()["active"] is True

    refreshed = client.get("/api/me/recommendations", params={"limit": 10}, headers=headers)
    refreshed_ids = {item["movie_id"] for item in refreshed.json()["items"]}
    assert movie_id not in refreshed_ids


def test_recommendation_feedback_save_for_later_reason(client: TestClient) -> None:
    headers = _register_user_headers(client)

    initial = client.get("/api/me/recommendations", params={"limit": 10}, headers=headers)
    assert initial.status_code == 200
    items = initial.json()["items"]
    assert items
    movie_id = items[0]["movie_id"]

    save_response = client.post(
        "/api/me/recommendations/feedback",
        json={
            "movie_id": movie_id,
            "event_type": "SAVE_FOR_LATER",
            "active": True,
        },
        headers=headers,
    )
    assert save_response.status_code == 200
    assert save_response.json()["event_type"] == "SAVE_FOR_LATER"

    updated = client.get("/api/me/recommendations", params={"limit": 10}, headers=headers)
    updated_items = updated.json()["items"]
    assert updated_items
    selected = next((item for item in updated_items if item["movie_id"] == movie_id), None)
    assert selected is not None
    assert selected["reason"] == "Saved for later"


def test_recommendation_event_tracking_endpoint(client: TestClient) -> None:
    headers = _register_user_headers(client)
    response = client.get("/api/me/recommendations", params={"limit": 10}, headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    movie_id = items[0]["movie_id"]

    track_response = client.post(
        "/api/me/recommendations/events",
        headers=headers,
        json={"movie_id": movie_id, "event_type": "CLICK"},
    )
    assert track_response.status_code == 200
    assert track_response.json()["recorded"] is True


def test_admin_sales_report_endpoint(client: TestClient) -> None:
    response = client.get("/api/admin/reports/sales", params={"limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert "paid_orders" in payload
    assert "gross_revenue_cents" in payload
    assert "showtimes" in payload
    assert "recommendation_clicks" in payload
