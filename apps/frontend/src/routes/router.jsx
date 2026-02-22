import { createBrowserRouter } from "react-router-dom";

import { AdminDashboardPage } from "../pages/AdminDashboardPage";
import { AppShell } from "../components/AppShell";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { CheckoutProcessingPage } from "../pages/CheckoutProcessingPage";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { MyTicketsPage } from "../pages/MyTicketsPage";
import { MovieDetailPage } from "../pages/MovieDetailPage";
import { MoviesPage } from "../pages/MoviesPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { RegisterPage } from "../pages/RegisterPage";
import { RouteErrorPage } from "../pages/RouteErrorPage";
import { SeatSelectionPage } from "../pages/SeatSelectionPage";
import { TicketScannerPage } from "../pages/TicketScannerPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      { path: "movies", element: <MoviesPage /> },
      { path: "movies/:movieId", element: <MovieDetailPage /> },
      {
        path: "me/tickets",
        element: (
          <ProtectedRoute>
            <MyTicketsPage />
          </ProtectedRoute>
        )
      },
      {
        path: "scan",
        element: (
          <ProtectedRoute roles={["ADMIN"]}>
            <TicketScannerPage />
          </ProtectedRoute>
        )
      },
      {
        path: "checkout/processing",
        element: (
          <ProtectedRoute>
            <CheckoutProcessingPage />
          </ProtectedRoute>
        )
      },
      {
        path: "admin",
        element: (
          <ProtectedRoute roles={["ADMIN"]}>
            <AdminDashboardPage />
          </ProtectedRoute>
        )
      },
      {
        path: "showtimes/:showtimeId/seats",
        element: (
          <ProtectedRoute>
            <SeatSelectionPage />
          </ProtectedRoute>
        )
      },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
]);
