import { Link } from "react-router-dom";

export function BrandLogo() {
  return (
    <Link className="brand-logo" to="/">
      <span className="brand-mark" aria-hidden="true">
        <span className="brand-mark-ring" />
        <span className="brand-mark-core" />
      </span>
      <span className="brand-copy">
        <strong>Big Apple Cinemas</strong>
        <small>Premium movie booking</small>
      </span>
    </Link>
  );
}
