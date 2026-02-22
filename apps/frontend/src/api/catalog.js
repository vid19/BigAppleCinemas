const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
export const AUTH_TOKEN_STORAGE_KEY = "bigapplecinemas.authToken";
export const REFRESH_TOKEN_STORAGE_KEY = "bigapplecinemas.refreshToken";
let accessToken = null;
let refreshToken = null;
let authRefreshHandler = null;

export function setAccessToken(token) {
  accessToken = token || null;
}

export function getAccessToken() {
  return accessToken;
}

export function setRefreshToken(token) {
  refreshToken = token || null;
}

export function getRefreshToken() {
  return refreshToken;
}

export function setAuthRefreshHandler(handler) {
  authRefreshHandler = handler;
}

async function request(
  path,
  { params = {}, method = "GET", body, headers = {}, noAuthRetry = false } = {}
) {
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
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!response.ok) {
    if (response.status === 401 && !noAuthRetry && typeof authRefreshHandler === "function") {
      const refreshed = await authRefreshHandler();
      if (refreshed) {
        return request(path, { params, method, body, headers, noAuthRetry: true });
      }
    }
    let detail = "";
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = `: ${payload.detail}`;
      }
    } catch {
      // no-op
    }
    const error = new Error(`Request failed with status ${response.status}${detail}`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function fetchMovies({ q = "", limit = 12, offset = 0 } = {}) {
  return request("/movies", { params: { q, limit, offset } });
}

export function registerUser(payload) {
  return request("/auth/register", { method: "POST", body: payload });
}

export function loginUser(payload) {
  return request("/auth/login", { method: "POST", body: payload });
}

export function fetchAuthMe() {
  return request("/auth/me");
}

export function refreshAuthToken(payload) {
  return request("/auth/refresh", { method: "POST", body: payload, noAuthRetry: true });
}

export function logoutUser(payload) {
  return request("/auth/logout", { method: "POST", body: payload, noAuthRetry: true });
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

export function fetchCheckoutOrderStatus(orderId) {
  return request(`/checkout/orders/${orderId}`);
}

export function fetchMyTickets() {
  return request("/me/tickets");
}

export function fetchMyOrders() {
  return request("/me/orders");
}

export function fetchMyRecommendations({ limit = 8 } = {}) {
  return request("/me/recommendations", { params: { limit } });
}

export function submitRecommendationFeedback(payload) {
  return request("/me/recommendations/feedback", { method: "POST", body: payload });
}

export function submitRecommendationEvent(payload) {
  return request("/me/recommendations/events", { method: "POST", body: payload });
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

export function fetchAdminAuditoriums({ theaterId, limit = 100, offset = 0 } = {}) {
  return request("/admin/auditoriums", {
    params: { theater_id: theaterId, limit, offset }
  });
}

export function createAuditorium(payload) {
  return request("/admin/auditoriums", { method: "POST", body: payload });
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
