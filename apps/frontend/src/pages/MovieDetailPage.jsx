import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchMovie, fetchShowtimes } from "../api/catalog";

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
  return new Date().toISOString().slice(0, 10);
}

export function MovieDetailPage() {
  const { movieId } = useParams();
  const [selectedDate, setSelectedDate] = useState(todayDateInput);

  const parsedMovieId = Number(movieId);
  const showtimeQueryParams = useMemo(
    () => ({
      movieId: parsedMovieId,
      date: selectedDate,
      limit: 50,
      offset: 0
    }),
    [parsedMovieId, selectedDate]
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

  return (
    <section className="page">
      <div className="page-header">
        <h2>{movie.title}</h2>
        <p>
          {movie.rating} • {movie.runtime_minutes} min • Release {formatDate(movie.release_date)}
        </p>
      </div>

      <p className="movie-description">{movie.description || "Description coming soon."}</p>

      <div className="filter-row">
        <label htmlFor="show-date">Show date</label>
        <input
          id="show-date"
          type="date"
          value={selectedDate}
          onChange={(event) => setSelectedDate(event.target.value)}
        />
      </div>

      {showtimesQuery.isLoading && <p className="status">Loading showtimes...</p>}
      {showtimesQuery.isError && <p className="status error">Could not load showtimes.</p>}
      {!showtimesQuery.isLoading && !showtimesQuery.isError && showtimes.length === 0 && (
        <p className="status">No showtimes available for the selected date.</p>
      )}

      <div className="showtime-list">
        {showtimes.map((showtime) => (
          <article className="showtime-card" key={showtime.id}>
            <div>
              <h3>{showtime.theater_name}</h3>
              <p>{formatDateTime(showtime.starts_at)}</p>
            </div>
            <Link to={`/showtimes/${showtime.id}/seats`}>Select seats</Link>
          </article>
        ))}
      </div>
    </section>
  );
}
