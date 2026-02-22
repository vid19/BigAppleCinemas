import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function ProtectedRoute({ children, roles = [] }) {
  const location = useLocation();
  const { isReady, isAuthenticated, user } = useAuth();

  if (!isReady) {
    return <p className="status">Checking your session...</p>;
  }

  if (!isAuthenticated) {
    const redirectTo = `${location.pathname}${location.search}`;
    return <Navigate replace state={{ redirectTo }} to="/login" />;
  }

  if (roles.length > 0 && !roles.includes(user?.role)) {
    return <Navigate replace to="/" />;
  }

  return children;
}
