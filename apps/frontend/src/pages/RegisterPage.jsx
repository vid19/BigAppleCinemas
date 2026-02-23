import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (isAuthenticated) {
    return <Navigate replace to="/" />;
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({ email: form.email, password: form.password });
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
          <p className="hero-kicker">Create account</p>
          <h3>Get booking-ready in under one minute.</h3>
          <ul>
            <li>Keep all tickets and receipts in one dashboard</li>
            <li>Unlock personalized movie recommendations</li>
            <li>Continue bookings seamlessly on any device</li>
          </ul>
        </aside>
        <article className="auth-card">
          <p className="hero-kicker">Create account</p>
          <h2>Register</h2>
          <p>Set up your account to reserve seats and manage tickets.</p>
          <form className="auth-form" onSubmit={onSubmit}>
            <label>
              Email
              <input
                required
                type="email"
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
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
            <label>
              Confirm password
              <input
                required
                minLength={8}
                type="password"
                value={form.confirmPassword}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, confirmPassword: event.target.value }))
                }
              />
            </label>
            <button disabled={isSubmitting} type="submit">
              {isSubmitting ? "Creating account..." : "Create account"}
            </button>
          </form>
          {error && <p className="status error">{error}</p>}
          <p className="auth-footer">
            <span>Already have an account?</span>
            <Link className="auth-footer-link" to="/login">
              Sign in
            </Link>
          </p>
        </article>
      </div>
    </section>
  );
}
