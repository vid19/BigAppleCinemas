# Big Apple Cinemas

Production-grade movie ticketing platform built with FastAPI + React.

## Project Milestones

1. Foundation (repo, docker, app skeletons, CI, docs)
2. Catalog (movies/theaters/showtimes + admin CRUD)
3. Seat maps and showtime seat status generation
4. Concurrency-safe reservations with TTL holds
5. Stripe checkout + webhook order finalization
6. Ticket validation + reporting
7. Production hardening and load testing

## Monorepo Layout

- `apps/backend`: FastAPI API, SQLAlchemy models, Alembic, workers
- `apps/frontend`: React app (Vite + Router + TanStack Query)
- `.github/workflows`: CI/CD workflows
- `infra/`: infra stubs for NGINX/Prometheus/Grafana
- `docs/`: architecture, concurrency, payments, deployment notes
- `docs/api.md`: current API endpoint reference
- `docs/ux-design-brief.md`: UX strategy and deliverables for upcoming development
- `docs/phase-2-plan.md`: scheduled Phase 2 execution plan and git checkpoints
- `docs/phase-3-plan.md`: seat map + showtime seat inventory implementation schedule

## Local Development

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Git Workflow (Strict)

- Milestone baseline commit lands on `main`.
- Feature branch commits are merged to `main` after review.
- Push after each milestone/merge checkpoint.
