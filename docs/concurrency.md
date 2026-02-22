# Concurrency Strategy

## Core objective

Prevent seat oversell under concurrent reservation attempts.

## Transactional approach (implemented)

1. Start database transaction.
2. Lock `showtime_seat_status` rows with `SELECT ... FOR UPDATE` for requested seats.
3. Validate all seats are `AVAILABLE`.
4. Create reservation and reservation-seat rows.
5. Update seat status to `HELD` and attach `held_by_reservation_id`.
6. Commit.

## Expiration

- Expiry cleanup runs in two ways:
  - background periodic task (`reservation.expire_overdue` via Celery beat)
  - reservation API calls (create/get/delete) for immediate consistency
- Background task cadence is controlled by `RESERVATION_EXPIRY_SWEEP_SECONDS` (default 30s).
- On expiry:
  - active reservations with `expires_at <= now` become `EXPIRED`
  - matching `showtime_seat_status` rows are released back to `AVAILABLE`
- Expiration is idempotent: only active rows transition.

## Current API behavior

- `POST /api/reservations`:
  - performs lock-safe hold creation
  - returns `409` when one or more seats are already held/sold
- `DELETE /api/reservations/{id}`:
  - releases an active hold and marks reservation `CANCELED`
- `GET /api/reservations/{id}`:
  - returns current reservation state after applying expiry cleanup

## Pseudocode

```text
BEGIN;
SELECT * FROM showtime_seat_status
WHERE showtime_id=:showtime_id AND seat_id IN (...)
FOR UPDATE;

IF any seat.status != AVAILABLE:
  ROLLBACK; return 409

INSERT reservation(..., status=ACTIVE, expires_at=now+8m)
INSERT reservation_seats(...)
UPDATE showtime_seat_status
  SET status=HELD, held_by_reservation_id=:reservation_id
COMMIT;
```

## Ticket Entry Window

- Scanner validity is not only `ticket.status == VALID`.
- It also enforces `now <= showtime.ends_at + TICKET_ACTIVE_GRACE_MINUTES`.
- After this window, scan returns `INVALID` with an expired message and does not consume the ticket.
