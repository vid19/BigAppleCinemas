import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="page page-shell">
      <div className="page-header page-header-modern">
        <h2>Page not found</h2>
      </div>
      <p className="status">The page you requested does not exist in this build.</p>
      <Link className="home-inline-link" to="/">
        Back to home
      </Link>
    </section>
  );
}
