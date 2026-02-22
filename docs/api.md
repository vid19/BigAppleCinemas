# API Reference (Current)

Base URL: `http://localhost:8000/api`

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
- `POST /auth/login`

## Booking (Scaffold)

- `POST /reservations` (creates transactional seat hold with expiry)
- `GET /reservations/{reservation_id}`
- `DELETE /reservations/{reservation_id}` (release hold early)
- `POST /tickets/scan`

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
