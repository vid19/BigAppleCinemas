const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, params = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

export function fetchMovies({ q = "", limit = 12, offset = 0 } = {}) {
  return request("/movies", { q, limit, offset });
}

export function fetchMovie(movieId) {
  return request(`/movies/${movieId}`);
}

export function fetchShowtimes({ movieId, date, limit = 20, offset = 0 } = {}) {
  return request("/showtimes", { movie_id: movieId, date, limit, offset });
}
