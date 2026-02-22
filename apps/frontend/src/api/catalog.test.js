import { afterEach, describe, expect, it, vi } from "vitest";

import {
  cancelReservation,
  confirmDemoCheckout,
  createMovie,
  createCheckoutSession,
  createReservation,
  deleteMovie,
  fetchMovies,
  fetchShowtimeSeats
} from "./catalog";

afterEach(() => {
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
});
