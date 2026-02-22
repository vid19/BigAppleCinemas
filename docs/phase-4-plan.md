# Phase 4 Plan: Concurrency-Safe Reservations

## Phase Goal

Add transactional seat holds with expiry so seats cannot be oversold under concurrent access.

## Scope

- Implement `POST /api/reservations` using row-level locking on `showtime_seat_status`.
- Prevent double-booking by rejecting non-available seats with `409 Conflict`.
- Add reservation expiry cleanup and early release endpoint.
- Integrate frontend seat page with hold creation, release, and countdown UX.

## Milestone Commits

- `feat(reservations): add lock-safe seat hold service and endpoints`
- `feat(frontend): connect seat selection to reservation hold countdown`
- `test: add reservation integration tests for hold conflict and release`
- `docs: update api and reservation phase notes`

## Definition of Done

- Holding the same seat twice concurrently is blocked by backend state transitions.
- Seat status changes to `HELD` on reservation and back to `AVAILABLE` on release/expiry.
- Frontend displays hold timer and surfaces hold/release errors clearly.
- CI checks pass.
