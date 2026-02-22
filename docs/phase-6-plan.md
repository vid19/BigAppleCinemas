# Phase 6 Plan: Ticket Validation + User Portal + Admin Sales Snapshot

## Phase Goal

Ship end-to-end ticket operations after payment:
- scan and validate tickets at entry
- let users view tickets/orders
- let admins view sales and occupancy snapshot

## Scope

- `POST /api/tickets/scan` with atomic `VALID -> USED` transition.
- `GET /api/me/tickets` and `GET /api/me/orders`.
- `GET /api/admin/reports/sales`.
- Frontend pages:
  - `/me/tickets`
  - `/scan`
  - admin sales snapshot card.

## Milestone Commits

- `feat(tickets): add atomic scan endpoint with used-state protection`
- `feat(portal): add my tickets and orders APIs + frontend page`
- `feat(admin): add sales snapshot api and dashboard card`
- `test: add portal and scanner integration coverage`
- `docs: update api and phase 6 plan`

## Definition of Done

- Scan endpoint returns `VALID`, `ALREADY_USED`, or `INVALID`.
- Scanning valid ticket twice does not allow second entry.
- User can view historical paid orders and tickets.
- Admin can see paid-orders/revenue/occupancy snapshot.
