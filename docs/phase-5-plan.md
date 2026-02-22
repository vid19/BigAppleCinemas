# Phase 5 Plan: Checkout + Payment Finalization

## Phase Goal

Implement checkout session creation and webhook-safe order finalization so reservations become paid
orders with generated tickets.

## Scope

- Create pending orders from active reservations (`POST /api/checkout/session`).
- Calculate pricing on server from seat types.
- Finalize paid orders in one transaction:
  - reservation `ACTIVE` -> `COMPLETED`
  - showtime seats `HELD` -> `SOLD`
  - create ticket rows with QR tokens
- Add Stripe webhook endpoint with Redis event idempotency guard.
- Add local demo confirm endpoint to simulate payment completion quickly.

## Milestone Commits

- `feat(checkout): add order session creation and finalize service`
- `feat(api): add stripe webhook idempotency and demo confirm endpoint`
- `feat(frontend): add checkout processing page and payment simulation flow`
- `test: add checkout and webhook integration coverage`
- `docs: update api and payment flow references`

## Definition of Done

- Checkout session endpoint returns pending order details and session identifier.
- Paid finalization marks seats sold and produces tickets exactly once.
- Duplicate webhook events do not reprocess finalized orders.
- Frontend supports hold -> checkout -> paid confirmation demo path.
