import { afterEach, describe, expect, it, vi } from "vitest";

import {
  cancelReservation,
  confirmDemoCheckout,
  createCheckoutSession,
  createMovie,
  createReservation,
  deleteMovie,
  fetchAuthMe,
  fetchCheckoutOrderStatus,
  fetchAdminSalesReport,
  fetchActiveReservation,
  fetchMyOrders,
  fetchMyRecommendations,
  fetchMyTickets,
  fetchMovies,
  fetchShowtimes,
  fetchShowtimeSeats,
  loginUser,
  logoutUser,
  refreshAuthToken,
  registerUser,
  setAccessToken,
  submitRecommendationEvent,
  submitRecommendationFeedback,
  scanTicket
} from "./catalog";

afterEach(() => {
  setAccessToken(null);
  vi.restoreAllMocks();
});

describe("catalog api client", () => {
  it("builds query params for movie list requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [], total: 0, limit: 10, offset: 20 })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchMovies({ q: "sky", limit: 10, offset: 20 });

    expect(result.total).toBe(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [requestUrl] = fetchMock.mock.calls[0];
    expect(requestUrl).toContain("/api/movies");
    expect(requestUrl).toContain("q=sky");
    expect(requestUrl).toContain("limit=10");
    expect(requestUrl).toContain("offset=20");
  });

  it("returns null for 204 delete responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: async () => ({})
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await deleteMovie(42);

    expect(result).toBeNull();
    const [requestUrl, requestOptions] = fetchMock.mock.calls[0];
    expect(requestUrl).toContain("/api/admin/movies/42");
    expect(requestOptions.method).toBe("DELETE");
  });

  it("requests seat inventory for a showtime", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ showtime_id: 7, seats: [] })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchShowtimeSeats(7);

    expect(result.showtime_id).toBe(7);
    const [requestUrl] = fetchMock.mock.calls[0];
    expect(requestUrl).toContain("/api/showtimes/7/seats");
  });

  it("includes include_past flag for showtime requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [], total: 0, limit: 5, offset: 0 })
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchShowtimes({ movieId: 7, includePast: true, limit: 5, offset: 0 });

    const [requestUrl] = fetchMock.mock.calls[0];
    expect(requestUrl).toContain("/api/showtimes");
    expect(requestUrl).toContain("movie_id=7");
    expect(requestUrl).toContain("include_past=true");
  });

  it("surfaces api detail in thrown errors", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid payload" })
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createMovie({
        title: "",
        description: "",
        runtime_minutes: 0,
        rating: "PG"
      })
    ).rejects.toThrow("Request failed with status 400: Invalid payload");
  });

  it("creates and cancels reservations", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ id: 22, status: "ACTIVE", seat_ids: [3, 4] })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => ({})
      });
    vi.stubGlobal("fetch", fetchMock);

    const reservation = await createReservation({ showtime_id: 8, seat_ids: [3, 4] });
    const canceled = await cancelReservation(22);

    expect(reservation.id).toBe(22);
    expect(canceled).toBeNull();
    const [createUrl, createOptions] = fetchMock.mock.calls[0];
    expect(createUrl).toContain("/api/reservations");
    expect(createOptions.method).toBe("POST");
    const [cancelUrl, cancelOptions] = fetchMock.mock.calls[1];
    expect(cancelUrl).toContain("/api/reservations/22");
    expect(cancelOptions.method).toBe("DELETE");
  });

  it("fetches active reservation for a showtime", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 31, status: "ACTIVE", showtime_id: 8, seat_ids: [3] })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchActiveReservation(8);

    expect(result.id).toBe(31);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/reservations/active");
    expect(fetchMock.mock.calls[0][0]).toContain("showtime_id=8");
  });

  it("creates checkout session and confirms demo payment", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({
          order_id: 9,
          provider_session_id: "cs_mock_123",
          status: "PENDING"
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ order_id: 9, order_status: "PAID", ticket_count: 2, tickets: [] })
      });
    vi.stubGlobal("fetch", fetchMock);

    const session = await createCheckoutSession({ reservation_id: 9 });
    const finalized = await confirmDemoCheckout({ order_id: 9 });

    expect(session.order_id).toBe(9);
    expect(finalized.order_status).toBe("PAID");
    expect(fetchMock.mock.calls[0][0]).toContain("/api/checkout/session");
    expect(fetchMock.mock.calls[1][0]).toContain("/api/checkout/demo/confirm");
  });

  it("fetches checkout order status", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ order_id: 9, order_status: "PENDING", ticket_count: 0, tickets: [] })
    });
    vi.stubGlobal("fetch", fetchMock);

    const payload = await fetchCheckoutOrderStatus(9);
    expect(payload.order_id).toBe(9);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/checkout/orders/9");
  });

  it("fetches user portal data and sales report", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ items: [], total: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ items: [], total: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ paid_orders: 0, gross_revenue_cents: 0, showtimes: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ items: [], total: 0 })
      });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMyTickets();
    await fetchMyOrders();
    await fetchAdminSalesReport({ limit: 5 });
    await fetchMyRecommendations({ limit: 4 });

    expect(fetchMock.mock.calls[0][0]).toContain("/api/me/tickets");
    expect(fetchMock.mock.calls[1][0]).toContain("/api/me/orders");
    expect(fetchMock.mock.calls[2][0]).toContain("/api/admin/reports/sales");
    expect(fetchMock.mock.calls[2][0]).toContain("limit=5");
    expect(fetchMock.mock.calls[3][0]).toContain("/api/me/recommendations");
    expect(fetchMock.mock.calls[3][0]).toContain("limit=4");
  });

  it("submits recommendation feedback payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ movie_id: 4, event_type: "SAVE_FOR_LATER", active: true })
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await submitRecommendationFeedback({
      movie_id: 4,
      event_type: "SAVE_FOR_LATER",
      active: true
    });

    expect(response.movie_id).toBe(4);
    const [requestUrl, requestOptions] = fetchMock.mock.calls[0];
    expect(requestUrl).toContain("/api/me/recommendations/feedback");
    expect(requestOptions.method).toBe("POST");
    expect(requestOptions.body).toContain('"event_type":"SAVE_FOR_LATER"');
  });

  it("records recommendation impression event", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ movie_id: 7, event_type: "IMPRESSION", recorded: true })
    });
    vi.stubGlobal("fetch", fetchMock);

    await submitRecommendationEvent({ movie_id: 7, event_type: "IMPRESSION" });

    expect(fetchMock.mock.calls[0][0]).toContain("/api/me/recommendations/events");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
  });

  it("sends staff header for ticket scan", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ result: "VALID", message: "ok" })
    });
    vi.stubGlobal("fetch", fetchMock);

    await scanTicket({ qr_token: "abc" }, { staffToken: "local-staff" });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers["x-staff-token"]).toBe("local-staff");
  });

  it("auth endpoints are callable", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ access_token: "token", refresh_token: "refresh", user: { id: 1 } })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ access_token: "token", refresh_token: "refresh", user: { id: 1 } })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ id: 1, email: "demo@bigapplecinemas.local", role: "ADMIN" })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ access_token: "new-token", refresh_token: "new-refresh", user: { id: 1 } })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => ({})
      });
    vi.stubGlobal("fetch", fetchMock);

    await registerUser({ email: "demo@bigapplecinemas.local", password: "Password123!" });
    await loginUser({ email: "demo@bigapplecinemas.local", password: "Password123!" });
    await fetchAuthMe();
    await refreshAuthToken({ refresh_token: "refresh" });
    await logoutUser({ refresh_token: "new-refresh" });

    expect(fetchMock.mock.calls[0][0]).toContain("/api/auth/register");
    expect(fetchMock.mock.calls[1][0]).toContain("/api/auth/login");
    expect(fetchMock.mock.calls[2][0]).toContain("/api/auth/me");
    expect(fetchMock.mock.calls[3][0]).toContain("/api/auth/refresh");
    expect(fetchMock.mock.calls[4][0]).toContain("/api/auth/logout");
  });

  it("adds authorization header when token is set", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [], total: 0 })
    });
    vi.stubGlobal("fetch", fetchMock);
    setAccessToken("token-123");

    await fetchMyTickets();

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer token-123");
  });
});
