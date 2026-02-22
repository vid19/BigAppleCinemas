import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <section className="page">
      <div className="hero-card">
        <p className="hero-kicker">Big Apple Cinemas</p>
        <h2>Book your next movie night in minutes</h2>
        <p>
          Browse movies, compare showtimes, and reserve your seats with a clean checkout flow.
        </p>
        <Link className="primary-link" to="/movies">
          Browse movies
        </Link>
      </div>
    </section>
  );
}
