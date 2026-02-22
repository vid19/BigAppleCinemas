# API Reference (Current)

Base URL: `http://localhost:8000/api`

## Request Context

- Every response includes `X-Request-ID` for request correlation.

## Public Catalog

- `GET /movies`
  - Query: `q`, `limit`, `offset`
- `GET /movies/{movie_id}`
- `GET /theaters`
  - Query: `city`, `limit`, `offset`
- `GET /showtimes`
  - Query: `movie_id`, `theater_id`, `date`, `limit`, `offset`
- `GET /showtimes/{showtime_id}/seats`
  - Returns seat map metadata + per-seat showtime status (`AVAILABLE`, `HELD`, `SOLD`)

## Auth (Scaffold)

- `POST /auth/register`
- `POST /auth/login` (rate limited)

## Booking (Scaffold)

- `POST /reservations` (creates transactional seat hold with expiry, rate limited)
- `GET /reservations/{reservation_id}`
- `DELETE /reservations/{reservation_id}` (release hold early)
- `POST /tickets/scan` (requires `x-staff-token`, rate limited)

## Checkout + Payments

- `POST /checkout/session`
  - Creates pending order from active reservation (server-side total calculation, rate limited)
- `POST /checkout/demo/confirm`
  - Local demo endpoint to finalize pending order as paid
- `POST /webhooks/stripe`
  - Idempotent webhook consumer for `checkout.session.completed`
  - Requires `x-webhook-secret` header

## User Portal

- `GET /me/tickets`
- `GET /me/orders`

## Admin Reports

- `GET /admin/reports/sales`

## Admin Catalog CRUD

### Movies

- `POST /admin/movies`
- `PATCH /admin/movies/{movie_id}`
- `DELETE /admin/movies/{movie_id}`

### Theaters

- `POST /admin/theaters`
- `PATCH /admin/theaters/{theater_id}`
- `DELETE /admin/theaters/{theater_id}`

### Showtimes

- `POST /admin/showtimes`
- `PATCH /admin/showtimes/{showtime_id}`
- `DELETE /admin/showtimes/{showtime_id}`

## Health

- `GET /health` (outside `/api`)
