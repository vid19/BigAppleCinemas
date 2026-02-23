import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchMovie, fetchShowtimes, fetchTheaters } from "../api/catalog";

function formatDate(dateValue) {
  if (!dateValue) {
    return "TBD";
  }
  return new Date(dateValue).toLocaleDateString();
}

function formatDateTime(dateValue) {
  return new Date(dateValue).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function todayDateInput() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function MovieDetailPage() {
  const { movieId } = useParams();
  const [selectedDate, setSelectedDate] = useState(todayDateInput);
  const [selectedTheaterId, setSelectedTheaterId] = useState("");

  const parsedMovieId = Number(movieId);
  const showtimeQueryParams = useMemo(
    () => ({
      movieId: parsedMovieId,
      theaterId: selectedTheaterId ? Number(selectedTheaterId) : undefined,
      date: selectedDate,
      limit: 50,
      offset: 0
    }),
    [parsedMovieId, selectedDate, selectedTheaterId]
  );

  const movieQuery = useQuery({
    queryKey: ["movie", parsedMovieId],
    queryFn: () => fetchMovie(parsedMovieId),
    enabled: Number.isFinite(parsedMovieId)
  });

  const showtimesQuery = useQuery({
    queryKey: ["showtimes", showtimeQueryParams],
    queryFn: () => fetchShowtimes(showtimeQueryParams),
    enabled: Number.isFinite(parsedMovieId)
  });

  const theatersQuery = useQuery({
    queryKey: ["theaters", { city: "", limit: 100, offset: 0 }],
    queryFn: () => fetchTheaters({ city: "", limit: 100, offset: 0 })
  });

  if (!Number.isFinite(parsedMovieId)) {
    return <p className="status error">Invalid movie URL.</p>;
  }

  if (movieQuery.isLoading) {
    return <p className="status">Loading movie details...</p>;
  }

  if (movieQuery.isError) {
    return <p className="status error">Could not load movie details.</p>;
  }

  const movie = movieQuery.data;
  const showtimes = showtimesQuery.data?.items ?? [];
  const theaters = theatersQuery.data?.items ?? [];
  const firstShowtime = showtimes[0];

  return (
    <section className="page page-shell">
      <div className="movie-detail-hero">
        <div className="movie-detail-poster">
          {movie.poster_url ? (
            <img src={movie.poster_url} alt={`${movie.title} poster`} />
          ) : (
            <span>{movie.title.slice(0, 1)}</span>
          )}
        </div>
        <div className="page-header page-header-modern">
          <h2>{movie.title}</h2>
          <p>
            {movie.rating} • {movie.runtime_minutes} min • Release {formatDate(movie.release_date)}
          </p>
        </div>
      </div>

      <p className="movie-description">{movie.description || "Description coming soon."}</p>
      <article className="movie-detail-insight-card">
        <p className="hero-kicker">Booking snapshot</p>
        <div className="movie-detail-insight-grid">
          <div>
            <span>Showtimes found</span>
            <strong>{showtimes.length}</strong>
          </div>
          <div>
            <span>Theaters available</span>
            <strong>{theaters.length}</strong>
          </div>
          <div>
            <span>Next slot</span>
            <strong>{firstShowtime ? formatDateTime(firstShowtime.starts_at) : "No slots"}</strong>
          </div>
        </div>
      </article>

      <div className="filters-wrap filters-wrap-modern">
        <div className="filter-row">
          <label htmlFor="show-date">Show date</label>
          <input
            id="show-date"
            type="date"
            min={todayDateInput()}
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
          />
        </div>
        <div className="filter-row">
          <label htmlFor="show-theater">Theater</label>
          <select
            id="show-theater"
            value={selectedTheaterId}
            onChange={(event) => setSelectedTheaterId(event.target.value)}
          >
            <option value="">All theaters</option>
            {theaters.map((theater) => (
              <option key={theater.id} value={theater.id}>
                {theater.name} ({theater.city})
              </option>
            ))}
          </select>
        </div>
      </div>

      {showtimesQuery.isLoading && <p className="status">Loading showtimes...</p>}
      {showtimesQuery.isError && <p className="status error">Could not load showtimes.</p>}
      {theatersQuery.isError && (
        <p className="status error">Could not load theaters. Showing all theaters by default.</p>
      )}
      {!showtimesQuery.isLoading && !showtimesQuery.isError && showtimes.length === 0 && (
        <p className="status">
          No showtimes available for the selected filters. Try another date or theater.
        </p>
      )}

      <div className="showtime-list">
        {showtimes.map((showtime) => (
          <article className="showtime-card" key={showtime.id}>
            <div>
              <h3>{showtime.theater_name}</h3>
              <p>{formatDateTime(showtime.starts_at)}</p>
              <p className="showtime-status">{showtime.status}</p>
            </div>
            <Link to={`/showtimes/${showtime.id}/seats`}>Select seats</Link>
          </article>
        ))}
      </div>
    </section>
  );
}
