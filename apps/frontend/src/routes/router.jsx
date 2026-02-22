import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { HomePage } from "../pages/HomePage";
import { MoviesPage } from "../pages/MoviesPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { RouteErrorPage } from "../pages/RouteErrorPage";
import { SeatSelectionPage } from "../pages/SeatSelectionPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "movies", element: <MoviesPage /> },
      { path: "showtimes/:showtimeId/seats", element: <SeatSelectionPage /> },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
]);
