# Phase 7 Plan: Production Hardening

## Phase Goal

Improve operational safety and production readiness for high-traffic and abuse scenarios.

## Scope

- Add Redis-backed rate limiting for critical endpoints:
  - `POST /api/auth/login`
  - `POST /api/reservations`
  - `POST /api/checkout/session`
  - `POST /api/tickets/scan`
- Add request correlation IDs (`X-Request-ID`) for every API response.
- Expand tests for hardening behavior:
  - rate-limit enforcement
  - request-id response header
- Document new headers and `429` behavior in API docs.

## Definition of Done

- Rate-limited endpoints return `429` when thresholds are exceeded.
- Every request returns a correlation ID header.
- CI remains green with hardening tests included.
