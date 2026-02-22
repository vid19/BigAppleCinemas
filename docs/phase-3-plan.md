# Phase 3 Plan: Seat Maps + Seat Inventory

## Phase Goal

Implement seat map rendering and showtime-scoped seat inventory so the booking flow has real
seat availability data before hold/checkout logic lands in Phase 4.

## Scope for Phase 3

- Seed auditorium seat map + seat rows for local/demo environments.
- Generate and maintain `showtime_seat_status` inventory per showtime.
- Expose `GET /api/showtimes/{id}/seats` for frontend seat map rendering.
- Build responsive seat-selection UI with status legend and selection summary.
- Add integration and frontend coverage for seat inventory fetch/render paths.

## Milestone Commits

- `feat(backend): seed and sync showtime seat inventory`
- `feat(api): add showtime seat map endpoint`
- `feat(frontend): render responsive seat selection from live inventory`
- `test: add seat inventory integration and client coverage`
- `docs: document phase 3 seat map architecture and api updates`

## Definition of Done

- Seeded environments have real seats attached to auditoriums.
- Each showtime has seat status rows ready for reservation logic.
- Seat selection page renders dynamic availability from backend data.
- Backend and frontend CI checks pass.
