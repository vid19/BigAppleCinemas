import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchMovies } from "../api/catalog";

const PAGE_SIZE = 12;

export function MoviesPage() {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);

  const offset = page * PAGE_SIZE;
  const queryParams = useMemo(
    () => ({ q: query.trim(), limit: PAGE_SIZE, offset }),
    [query, offset]
  );

  const moviesQuery = useQuery({
    queryKey: ["movies", queryParams],
    queryFn: () => fetchMovies(queryParams)
  });

  const data = moviesQuery.data;
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasPrevious = page > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <section className="page page-shell movies-page-modern">
      <div className="page-header page-header-modern">
        <h2>Movies</h2>
        <p>Discover what is playing now and jump straight into seat booking.</p>
      </div>

      <article className="movies-hero-band">
        <p className="hero-kicker">Now showing</p>
        <h3>Plan tonight with live showtimes and fast seat selection.</h3>
        <p>
          Search by title, open a movie, and move straight to a theater/time combination that works
          for your schedule.
        </p>
      </article>

      <div className="search-row search-row-modern">
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(0);
          }}
          placeholder="Search by title"
          aria-label="Search movies"
        />
      </div>

      {moviesQuery.isLoading && <p className="status">Loading movies...</p>}
      {moviesQuery.isError && (
        <p className="status error">
          Failed to load movies. Ensure backend is running and try again.
        </p>
      )}

      {!moviesQuery.isLoading && !moviesQuery.isError && items.length === 0 && (
        <p className="status">No movies found for this search.</p>
      )}

      {!moviesQuery.isLoading && !moviesQuery.isError && items.length > 0 && (
        <p className="movies-count-note">
          Showing {items.length} of {total} movie{total === 1 ? "" : "s"}.
        </p>
      )}

      <div className="movie-grid">
        {items.map((movie) => (
          <article className="movie-card" key={movie.id}>
            <div className="movie-poster-fallback">
              {movie.poster_url ? (
                <img src={movie.poster_url} alt={`${movie.title} poster`} />
              ) : (
                <span>{movie.title.slice(0, 1)}</span>
              )}
            </div>
            <div className="movie-card-body">
              <h3>{movie.title}</h3>
              <p>
                {movie.rating} • {movie.runtime_minutes} min
              </p>
              <Link to={`/movies/${movie.id}`}>View showtimes</Link>
            </div>
          </article>
        ))}
      </div>

      <div className="pagination-row">
        <button type="button" disabled={!hasPrevious} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span>
          Page {page + 1} • {total} total
        </span>
        <button type="button" disabled={!hasNext} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>
    </section>
  );
}
