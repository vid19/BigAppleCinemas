# Architecture

## High-level

- React SPA consumes FastAPI REST endpoints.
- PostgreSQL is the system of record.
- Redis is used for cache, ephemeral holds, and queue broker.
- Celery workers handle expiration/email jobs.

## Service Boundaries

- `apps/backend/app/api`: HTTP interface and request validation.
- `apps/backend/app/services`: transactional business logic.
- `apps/backend/app/models`: persistence model.
- `apps/frontend/src/pages`: user and admin surfaces.

## Catalog Caching

- Read-heavy catalog endpoints (`/movies`, `/movies/{id}`, `/theaters`, `/showtimes`) are cached in Redis.
- Cache keys use the `catalog:*` prefix and include query parameters for deterministic lookups.
- Admin catalog writes invalidate `catalog:*` key groups to keep read responses fresh.
