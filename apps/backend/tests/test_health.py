from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Request-ID")


def test_metrics_endpoint_exposes_counters(client: TestClient) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    payload = response.text
    assert "app_requests_total" in payload
    assert "reservation_attempt_total" in payload
    assert "ticket_scan_attempt_total" in payload
