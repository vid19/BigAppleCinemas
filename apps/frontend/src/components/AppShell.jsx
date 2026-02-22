import { Link, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div className="layout">
      <header className="header">
        <h1>Big Apple Cinemas</h1>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/movies">Movies</Link>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
