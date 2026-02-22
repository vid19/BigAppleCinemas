# Deployment

## Local

- `docker compose up --build`
- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Background workers:
  - `worker` service executes async jobs
  - `beat` service schedules periodic jobs (reservation expiry sweep)
- Redis is also used for API rate-limiting and webhook idempotency keys.

## Target platforms

- API + workers: Fly.io / Render / Railway
- Frontend: Vercel / Netlify
- Managed Postgres + Redis in production

## CI/CD workflow

- CI pipeline: `.github/workflows/ci.yml`
  - backend lint + tests
  - frontend lint + tests
- Deploy pipeline: `.github/workflows/deploy.yml`
  - Staging deployment on pushes to `main` (if staging deploy secrets are configured)
  - Manual staging/production deployment via workflow dispatch
  - Migration step runs before backend/frontend deploy commands

## Deploy secret checklist

- See `docs/environment.md` for required staging and production deploy secrets.
