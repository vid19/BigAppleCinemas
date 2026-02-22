import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchMovies } from "../api/catalog";

const BOOKING_STEPS = [
  {
    title: "Pick a movie",
    description: "Browse now playing titles and compare theaters in a few taps."
  },
  {
    title: "Choose your seats",
    description: "Seat states update live so you can lock the exact spots you want."
  },
  {
    title: "Checkout securely",
    description: "Complete payment, then access QR tickets instantly from My Tickets."
  }
];

export function HomePage() {
  const moviesQuery = useQuery({
    queryKey: ["home-featured-movies"],
    queryFn: () => fetchMovies({ limit: 4, offset: 0 }),
    staleTime: 60_000
  });

  const featuredMovies = moviesQuery.data?.items ?? [];

  return (
    <section className="page home-page">
      <div className="hero-card">
        <p className="hero-kicker">Big Apple Cinemas</p>
        <h2>Book your next movie night in minutes</h2>
        <p>
          Browse movies, compare showtimes, reserve seats for 8 minutes, and checkout with secure
          ticket delivery.
        </p>
        <div className="hero-actions">
          <Link className="primary-link" to="/movies">
            Browse movies
          </Link>
          <Link className="secondary-link" to="/my/tickets">
            View my tickets
          </Link>
        </div>
      </div>

      <div className="home-layout">
        <section className="home-panel">
          <div className="home-panel-header">
            <h3>Now playing</h3>
            <Link to="/movies">See all</Link>
          </div>

          {moviesQuery.isLoading && <p className="status">Loading featured movies...</p>}
          {moviesQuery.isError && (
            <p className="status error">
              Could not load featured movies. Browse the full catalog from the Movies page.
            </p>
          )}
          {!moviesQuery.isLoading && !moviesQuery.isError && featuredMovies.length === 0 && (
            <p className="status">No movies available right now. Check back shortly.</p>
          )}

          <div className="home-movie-grid">
            {featuredMovies.map((movie) => (
              <article className="home-movie-card" key={movie.id}>
                <h4>{movie.title}</h4>
                <p>
                  {movie.rating} • {movie.runtime_minutes} min
                </p>
                <Link to={`/movies/${movie.id}`}>Showtimes</Link>
              </article>
            ))}
          </div>
        </section>

        <div className="home-side-stack">
          <section className="home-panel home-metric-grid">
            <article>
              <p>8 min</p>
              <span>Seat hold window</span>
            </article>
            <article>
              <p>QR</p>
              <span>Instant ticket delivery</span>
            </article>
            <article>
              <p>24/7</p>
              <span>Scan and validation ready</span>
            </article>
          </section>

          <section className="home-panel">
            <h3>Tonight quick start</h3>
            <p className="home-muted">
              Start with movies, select a showtime, lock seats, and finish checkout in under
              2 minutes.
            </p>
            <Link className="home-inline-link" to="/movies">
              Find showtimes
            </Link>
          </section>
        </div>
      </div>

      <section className="home-panel">
        <h3>Book in 3 simple steps</h3>
        <div className="home-steps-grid">
          {BOOKING_STEPS.map((step, index) => (
            <article className="home-step-card" key={step.title}>
              <span>Step {index + 1}</span>
              <h4>{step.title}</h4>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
