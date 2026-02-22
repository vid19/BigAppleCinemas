import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HomePage } from "./HomePage";
import { MovieDetailPage } from "./MovieDetailPage";
import { MoviesPage } from "./MoviesPage";
import { MyTicketsPage } from "./MyTicketsPage";
import { SeatSelectionPage } from "./SeatSelectionPage";

const useQueryMock = vi.fn();
const useMutationMock = vi.fn();
const useQueryClientMock = vi.fn();
const useAuthMock = vi.fn();
let paramsMock = { movieId: "3" };

vi.mock("@tanstack/react-query", () => ({
  useQuery: (options) => useQueryMock(options),
  useMutation: (options) => useMutationMock(options),
  useQueryClient: () => useQueryClientMock()
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => paramsMock
  };
});

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => useAuthMock()
}));

function renderPage(element) {
  return renderToStaticMarkup(<MemoryRouter>{element}</MemoryRouter>);
}

beforeEach(() => {
  paramsMock = { movieId: "3" };
  useQueryMock.mockReset();
  useMutationMock.mockReset();
  useQueryClientMock.mockReset();
  useAuthMock.mockReset();
  useAuthMock.mockReturnValue({
    isAuthenticated: false
  });
  useMutationMock.mockReturnValue({
    mutate: vi.fn(),
    isPending: false
  });
  useQueryClientMock.mockReturnValue({
    invalidateQueries: vi.fn()
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("catalog pages", () => {
  it("renders movie cards on movies page", () => {
    useQueryMock.mockImplementation(({ queryKey }) => {
      if (queryKey[0] === "movies") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [
              {
                id: 1,
                title: "Skyline Heist",
                runtime_minutes: 126,
                rating: "PG-13",
                poster_url: null
              }
            ],
            total: 1
          }
        };
      }

      return { isLoading: false, isError: false, data: {} };
    });

    const html = renderPage(<MoviesPage />);

    expect(html).toContain("Skyline Heist");
    expect(html).toContain("View showtimes");
    expect(html).toContain("Page 1");
  });

  it("renders theater filters and showtimes on movie detail page", () => {
    useQueryMock.mockImplementation(({ queryKey }) => {
      if (queryKey[0] === "movie") {
        return {
          isLoading: false,
          isError: false,
          data: {
            id: 3,
            title: "The Last Encore",
            description: "A comeback drama.",
            runtime_minutes: 104,
            rating: "PG",
            release_date: "2025-12-17",
            poster_url: null
          }
        };
      }
      if (queryKey[0] === "showtimes") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [
              {
                id: 11,
                theater_name: "Big Apple Cinemas - Midtown",
                starts_at: "2026-02-22T10:00:00Z",
                status: "SCHEDULED"
              }
            ]
          }
        };
      }
      if (queryKey[0] === "theaters") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [{ id: 1, name: "Big Apple Cinemas - Midtown", city: "New York" }]
          }
        };
      }
      return { isLoading: false, isError: false, data: {} };
    });

    const html = renderPage(<MovieDetailPage />);

    expect(html).toContain("The Last Encore");
    expect(html).toContain("All theaters");
    expect(html).toContain("Select seats");
    expect(html).toContain("SCHEDULED");
  });

  it("renders interactive seat inventory details on seat selection page", () => {
    paramsMock = { showtimeId: "11" };
    useQueryMock.mockImplementation(({ queryKey }) => {
      if (queryKey[0] === "showtime-seats") {
        return {
          isLoading: false,
          isError: false,
          data: {
            showtime_id: 11,
            movie_id: 3,
            theater_name: "Big Apple Cinemas - Midtown",
            starts_at: "2026-02-22T10:00:00Z",
            seatmap_name: "Auditorium 1 Standard Layout",
            seats: [
              {
                seat_id: 1,
                seat_code: "A1",
                row_label: "A",
                seat_number: 1,
                seat_type: "VIP",
                status: "AVAILABLE"
              },
              {
                seat_id: 2,
                seat_code: "A2",
                row_label: "A",
                seat_number: 2,
                seat_type: "VIP",
                status: "SOLD"
              }
            ]
          }
        };
      }
      return { isLoading: false, isError: false, data: {} };
    });

    const html = renderPage(<SeatSelectionPage />);

    expect(html).toContain("Select your seats");
    expect(html).toContain("Booking summary");
    expect(html).toContain("A1");
    expect(html).toContain("Hold seats");
  });

  it("renders my tickets and orders sections", () => {
    useQueryMock.mockImplementation(({ queryKey }) => {
      if (queryKey[0] === "me-tickets") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [
              {
                ticket_id: 1,
                order_id: 7,
                qr_token: "tkt_123",
                ticket_status: "VALID",
                seat_code: "B4",
                seat_type: "PREMIUM",
                movie_title: "Skyline Heist",
                theater_name: "Big Apple Cinemas - Midtown",
                showtime_id: 5,
                showtime_starts_at: "2026-02-23T14:00:00Z",
                used_at: null,
                created_at: "2026-02-20T14:00:00Z"
              }
            ],
            total: 1
          }
        };
      }
      if (queryKey[0] === "me-orders") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [
              {
                order_id: 7,
                reservation_id: 3,
                showtime_id: 5,
                status: "PAID",
                total_cents: 3200,
                currency: "USD",
                provider: "MOCK_STRIPE",
                ticket_count: 1,
                created_at: "2026-02-20T14:00:00Z"
              }
            ],
            total: 1
          }
        };
      }
      return { isLoading: false, isError: false, data: {} };
    });

    const html = renderPage(<MyTicketsPage />);

    expect(html).toContain("My Tickets");
    expect(html).toContain("Active tickets");
    expect(html).toContain("Skyline Heist");
    expect(html).toContain("Order #7");
  });

  it("renders personalized recommendations when user is authenticated", () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true
    });
    useQueryMock.mockImplementation(({ queryKey }) => {
      if (queryKey[0] === "home-featured-movies") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [
              {
                id: 1,
                title: "Skyline Heist",
                description: "Action thriller",
                runtime_minutes: 126,
                rating: "PG-13",
                poster_url: null
              }
            ],
            total: 1
          }
        };
      }
      if (queryKey[0] === "home-recommendations") {
        return {
          isLoading: false,
          isError: false,
          data: {
            items: [
              {
                movie_id: 5,
                title: "Midnight Orbit",
                reason: "Because you watch Sci-Fi movies",
                next_showtime_starts_at: "2026-02-24T02:00:00Z",
                poster_url: null
              }
            ],
            total: 1
          }
        };
      }
      return { isLoading: false, isError: false, data: {} };
    });

    const html = renderPage(<HomePage />);

    expect(html).toContain("Recommended for you");
    expect(html).toContain("Midnight Orbit");
    expect(html).toContain("Because you watch Sci-Fi movies");
    expect(html).toContain("Save for later");
    expect(html).toContain("Not interested");
  });
});
