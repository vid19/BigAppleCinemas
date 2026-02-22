import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section>
      <h2>Page not found</h2>
      <p>The page you requested does not exist in this build yet.</p>
      <p>
        Go back to <Link to="/">Home</Link>.
      </p>
    </section>
  );
}
