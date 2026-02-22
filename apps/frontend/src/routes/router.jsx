import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { HomePage } from "../pages/HomePage";
import { MoviesPage } from "../pages/MoviesPage";
import { SeatSelectionPage } from "../pages/SeatSelectionPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "movies", element: <MoviesPage /> },
      { path: "showtimes/:showtimeId/seats", element: <SeatSelectionPage /> }
    ]
  }
]);
