# Payments

## Provider

`MOCK_STRIPE` is used for local development and integration testing.
Production target remains Stripe Checkout + webhook finalization.

## Safety rules

- Price is calculated server-side from seat type + rules.
- Client never controls final amount.
- Webhook secret validation is required (`x-webhook-secret`).
- Webhook event IDs are stored in Redis for idempotency.

## Finalization sequence

1. Receive `checkout.session.completed` webhook.
2. Verify webhook secret and idempotency event key.
3. In one transaction, convert held seats to sold and issue tickets.

## Current Endpoints

- `POST /api/checkout/session`
- `POST /api/checkout/demo/confirm` (local demo)
- `POST /api/webhooks/stripe`
