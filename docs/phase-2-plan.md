# Phase 2 Plan: Catalog + UX Integration

## Phase Goal

Implement catalog experience end-to-end for movies, theaters, and showtimes with responsive UX aligned to the design brief.

## Scope for Phase 2

- Backend catalog APIs (movies, theaters, showtimes).
- Admin CRUD for catalog entities (minimal viable controls).
- Frontend catalog pages and responsive layouts.
- Caching baseline for read-heavy catalog endpoints.
- UX foundation components from `docs/ux-design-brief.md`.

## Execution Schedule

### Week 1: Data + API Foundation

- Finalize Phase 2 schema additions/migrations for catalog fields.
- Implement backend read APIs:
  - `GET /api/movies`
  - `GET /api/movies/{id}`
  - `GET /api/theaters`
  - `GET /api/showtimes`
- Add pagination, filtering, and sorting basics.
- Add DB indexes for high-frequency catalog queries.

### Week 2: Admin Catalog CRUD + Seed Data

- Implement admin routes for movies/theaters/showtimes.
- Add request/response validation schemas.
- Add seed script for demo-ready data.
- Add initial caching strategy (Redis) for list endpoints.

### Week 3: Frontend Catalog UX

- Build movies list page with search/filter/sort UX.
- Build movie detail page with showtime selector.
- Build theater/date selector interaction patterns.
- Implement loading/empty/error states and skeletons.
- Ensure responsive behavior on 390/768/1440/1920 layouts.

### Week 4: Hardening + Docs + Demo Readiness

- Add backend integration tests for catalog endpoints.
- Add frontend component tests for filters and navigation.
- Measure and document API response performance.
- Update architecture/API docs and add screenshots.
- Prepare recruiter-ready walkthrough content.

## Strict Git Workflow for Phase 2

1. Create branch from `main`:
   - `git checkout main`
   - `git pull origin main`
   - `git checkout -b phase-2-catalog`
2. Implement one milestone at a time.
3. Commit per milestone with focused message.
4. Push each milestone commit:
   - `git push origin phase-2-catalog`
5. Open PR to `main` after each meaningful checkpoint.
6. Merge in GitHub only after CI is green.

## Recommended Milestone Commits

- `feat(backend): implement catalog read endpoints with filtering`
- `feat(admin): add movies theaters showtimes crud`
- `feat(frontend): build responsive movies list and details flows`
- `feat(cache): add redis caching for catalog queries`
- `test: add backend integration and frontend component tests`
- `docs: update phase 2 architecture api and screenshots`

## Definition of Done (Phase 2)

- Catalog APIs return real DB data with pagination/filter support.
- Admin can create/update/delete movies, theaters, and showtimes.
- Frontend catalog flows are responsive and usable across target breakpoints.
- CI passes backend and frontend jobs.
- Docs reflect implemented APIs and UX behavior.
- Project is demoable end-to-end for browse and showtime discovery.

## Dependencies and Assumptions

- PostgreSQL + Redis available in local and CI environments.
- Seed data script exists and can load demo catalog quickly.
- Design decisions from `docs/ux-design-brief.md` are followed for visual consistency.

## Progress Update (2026-02-22)

Completed:

- Catalog read APIs with filtering/pagination (`/movies`, `/movies/{id}`, `/theaters`, `/showtimes`).
- Local bootstrap for tables + demo catalog seed data.
- Frontend movie discovery flow with movie detail and theater/date showtime filters.
- Admin backend CRUD for movies/theaters/showtimes.
- Admin frontend dashboard for create/delete operations.
- Redis cache for catalog reads + cache invalidation on admin writes.
- Backend integration API tests and frontend API client unit tests.

Remaining in Phase 2:

- No open engineering tasks. Phase 2 deliverables were completed and merged.
- Screenshots/performance snapshots can be appended as optional recruiter packaging updates.
