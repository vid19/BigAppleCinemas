# Concurrency Strategy

## Core objective

Prevent seat oversell under concurrent reservation attempts.

## Planned transactional approach

1. Start database transaction.
2. Lock `showtime_seat_status` rows with `SELECT ... FOR UPDATE` for requested seats.
3. Validate all seats are `AVAILABLE`.
4. Create reservation and reservation-seat rows.
5. Update seat status to `HELD` and attach `held_by_reservation_id`.
6. Commit.

## Expiration

- Worker task expires reservations at TTL.
- Expiration is idempotent: only active rows transition.
