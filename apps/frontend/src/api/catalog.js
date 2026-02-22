const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, { params = {}, method = "GET", body, headers = {} } = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  const response = await fetch(url.toString(), {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = `: ${payload.detail}`;
      }
    } catch {
      // no-op
    }
    throw new Error(`Request failed with status ${response.status}${detail}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function fetchMovies({ q = "", limit = 12, offset = 0 } = {}) {
  return request("/movies", { params: { q, limit, offset } });
}

export function fetchMovie(movieId) {
  return request(`/movies/${movieId}`);
}

export function fetchShowtimes({
  movieId,
  theaterId,
  date,
  includePast = false,
  limit = 20,
  offset = 0
} = {}) {
  return request("/showtimes", {
    params: { movie_id: movieId, theater_id: theaterId, date, include_past: includePast, limit, offset }
  });
}

export function fetchShowtimeSeats(showtimeId) {
  return request(`/showtimes/${showtimeId}/seats`);
}

export function createReservation(payload) {
  return request("/reservations", { method: "POST", body: payload });
}

export function fetchReservation(reservationId) {
  return request(`/reservations/${reservationId}`);
}

export function fetchActiveReservation(showtimeId) {
  return request("/reservations/active", {
    params: { showtime_id: showtimeId }
  });
}

export function cancelReservation(reservationId) {
  return request(`/reservations/${reservationId}`, { method: "DELETE" });
}

export function createCheckoutSession(payload) {
  return request("/checkout/session", { method: "POST", body: payload });
}

export function confirmDemoCheckout(payload) {
  return request("/checkout/demo/confirm", { method: "POST", body: payload });
}

export function fetchMyTickets() {
  return request("/me/tickets");
}

export function fetchMyOrders() {
  return request("/me/orders");
}

export function scanTicket(payload, { staffToken } = {}) {
  return request("/tickets/scan", {
    method: "POST",
    body: payload,
    headers: staffToken ? { "x-staff-token": staffToken } : {}
  });
}

export function fetchAdminSalesReport({ limit = 10 } = {}) {
  return request("/admin/reports/sales", { params: { limit } });
}

export function fetchTheaters({ city = "", limit = 100, offset = 0 } = {}) {
  return request("/theaters", {
    params: { city, limit, offset }
  });
}

export function createMovie(payload) {
  return request("/admin/movies", { method: "POST", body: payload });
}

export function updateMovie(movieId, payload) {
  return request(`/admin/movies/${movieId}`, { method: "PATCH", body: payload });
}

export function deleteMovie(movieId) {
  return request(`/admin/movies/${movieId}`, { method: "DELETE" });
}

export function createTheater(payload) {
  return request("/admin/theaters", { method: "POST", body: payload });
}

export function updateTheater(theaterId, payload) {
  return request(`/admin/theaters/${theaterId}`, { method: "PATCH", body: payload });
}

export function deleteTheater(theaterId) {
  return request(`/admin/theaters/${theaterId}`, { method: "DELETE" });
}

export function createShowtime(payload) {
  return request("/admin/showtimes", { method: "POST", body: payload });
}

export function updateShowtime(showtimeId, payload) {
  return request(`/admin/showtimes/${showtimeId}`, { method: "PATCH", body: payload });
}

export function deleteShowtime(showtimeId) {
  return request(`/admin/showtimes/${showtimeId}`, { method: "DELETE" });
}
