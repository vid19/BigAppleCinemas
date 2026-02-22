import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="page">
      <h2>Page not found</h2>
      <p className="status">The page you requested does not exist in this build.</p>
      <Link to="/">Back to home</Link>
    </section>
  );
}
