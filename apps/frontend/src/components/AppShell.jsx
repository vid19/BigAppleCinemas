import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { BrandLogo } from "./BrandLogo";

function navClassName({ isActive }) {
  return `header-nav-link ${isActive ? "is-active" : ""}`;
}

export function AppShell() {
  const { isAuthenticated, isReady, logout, user } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  return (
    <div className="layout">
      <header className="header shell-wrap">
        <BrandLogo />
        <nav className="header-nav">
          <NavLink className={navClassName} to="/">
            Home
          </NavLink>
          <NavLink className={navClassName} to="/movies">
            Movies
          </NavLink>
          {isAuthenticated && (
            <NavLink className={navClassName} to="/me/tickets">
              My Tickets
            </NavLink>
          )}
          {isAdmin && (
            <NavLink className={navClassName} to="/scan">
              Scan
            </NavLink>
          )}
          {isAdmin && (
            <NavLink className={navClassName} to="/admin">
              Admin
            </NavLink>
          )}
          {!isReady && <span className="header-session">Loading...</span>}
          {isReady && !isAuthenticated && (
            <>
              <NavLink className={navClassName} to="/login">
                Login
              </NavLink>
              <NavLink className={navClassName} to="/register">
                Register
              </NavLink>
            </>
          )}
          {isReady && isAuthenticated && (
            <>
              <span className="header-session">{user?.email}</span>
              <button className="header-logout" onClick={logout} type="button">
                Logout
              </button>
            </>
          )}
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
