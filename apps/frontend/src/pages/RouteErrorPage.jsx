import { Link, isRouteErrorResponse, useRouteError } from "react-router-dom";

export function RouteErrorPage() {
  const error = useRouteError();

  let title = "Unexpected application error";
  let detail = "Something went wrong while loading this route.";

  if (isRouteErrorResponse(error)) {
    title = `${error.status} ${error.statusText}`;
    if (typeof error.data === "string" && error.data.trim()) {
      detail = error.data;
    } else if (error.status === 404) {
      detail = "The requested route was not found.";
    }
  } else if (error instanceof Error && error.message) {
    detail = error.message;
  }

  return (
    <section className="page page-shell">
      <div className="page-header page-header-modern">
        <h2>{title}</h2>
      </div>
      <p className="status error">{detail}</p>
      <Link className="home-inline-link" to="/">
        Back to home
      </Link>
    </section>
  );
}
