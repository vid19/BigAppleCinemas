from fastapi.testclient import TestClient


def _create_paid_ticket(client: TestClient) -> str:
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
    )
    assert reservation_response.status_code == 201
    reservation_id = reservation_response.json()["id"]

    checkout_response = client.post(
        "/api/checkout/session",
        json={"reservation_id": reservation_id},
    )
    assert checkout_response.status_code == 201
    order_id = checkout_response.json()["order_id"]

    confirm_response = client.post("/api/checkout/demo/confirm", json={"order_id": order_id})
    assert confirm_response.status_code == 200
    tickets = confirm_response.json()["tickets"]
    assert len(tickets) == 1
    return tickets[0]["qr_token"]


def test_ticket_scan_valid_then_already_used(client: TestClient) -> None:
    qr_token = _create_paid_ticket(client)

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


def test_me_endpoints_return_orders_and_tickets(client: TestClient) -> None:
    _create_paid_ticket(client)

    tickets_response = client.get("/api/me/tickets")
    orders_response = client.get("/api/me/orders")

    assert tickets_response.status_code == 200
    assert orders_response.status_code == 200
    assert tickets_response.json()["total"] >= 1
    assert orders_response.json()["total"] >= 1


def test_me_recommendations_endpoint_returns_ranked_movies(client: TestClient) -> None:
    _create_paid_ticket(client)

    tickets_response = client.get("/api/me/tickets")
    assert tickets_response.status_code == 200
    watched_movies = {item["movie_title"] for item in tickets_response.json()["items"]}

    response = client.get("/api/me/recommendations", params={"limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1
    first_item = payload["items"][0]
    assert "movie_id" in first_item
    assert "reason" in first_item
    assert isinstance(first_item["score"], float)
    assert first_item["title"] not in watched_movies


def test_admin_sales_report_endpoint(client: TestClient) -> None:
    response = client.get("/api/admin/reports/sales", params={"limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert "paid_orders" in payload
    assert "gross_revenue_cents" in payload
    assert "showtimes" in payload
