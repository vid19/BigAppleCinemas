import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.redirectTo || "/";
  const [form, setForm] = useState({
    email: "demo@bigapplecinemas.local",
    password: "DemoAdmin123!",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (isAuthenticated) {
    return <Navigate replace state={{ redirectTo }} to={redirectTo} />;
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login(form);
      navigate(redirectTo, { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page page-shell auth-page auth-page-modern">
      <div className="auth-split-card">
        <aside className="auth-side-panel">
          <p className="hero-kicker">Welcome back</p>
          <h3>Your next showtime is a few taps away.</h3>
          <ul>
            <li>Reserve seats with an 8-minute hold timer</li>
            <li>Checkout and receive QR tickets instantly</li>
            <li>Manage active and past tickets from one place</li>
          </ul>
        </aside>
        <article className="auth-card">
          <p className="hero-kicker">Account access</p>
          <h2>Sign in</h2>
          <p>Use your account to hold seats, checkout, and access admin tools.</p>
          <form className="auth-form" onSubmit={onSubmit}>
            <label>
              Email
              <input
                required
                type="email"
                value={form.email}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, email: event.target.value }))
                }
              />
            </label>
            <label>
              Password
              <input
                required
                minLength={8}
                type="password"
                value={form.password}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, password: event.target.value }))
                }
              />
            </label>
            <button disabled={isSubmitting} type="submit">
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
          {error && <p className="status error">{error}</p>}
          <p className="auth-footer">
            <span>New here?</span>
            <Link className="auth-footer-link" to="/register">
              Create account
            </Link>
          </p>
        </article>
      </div>
    </section>
  );
}
