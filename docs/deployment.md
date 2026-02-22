# Deployment

## Local

- `docker compose up --build`
- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Background workers:
  - `worker` service executes async jobs
  - `beat` service schedules periodic jobs (reservation expiry sweep)

## Target platforms

- API + workers: Fly.io / Render / Railway
- Frontend: Vercel / Netlify
- Managed Postgres + Redis in production
