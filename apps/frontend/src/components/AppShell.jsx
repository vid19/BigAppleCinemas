import { NavLink, Outlet } from "react-router-dom";

import { BrandLogo } from "./BrandLogo";

function navClassName({ isActive }) {
  return `header-nav-link ${isActive ? "is-active" : ""}`;
}

export function AppShell() {
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
          <NavLink className={navClassName} to="/me/tickets">
            My Tickets
          </NavLink>
          <NavLink className={navClassName} to="/scan">
            Scan
          </NavLink>
          <NavLink className={navClassName} to="/admin">
            Admin
          </NavLink>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
