# Payments

## Provider

Stripe Checkout is the default provider in the first implementation.

## Safety rules

- Price is calculated server-side from seat type + rules.
- Client never controls final amount.
- Webhook signature validation is mandatory.
- Webhook event IDs are stored for idempotency.

## Finalization sequence

1. Receive `checkout.session.completed` webhook.
2. Verify signature and idempotency.
3. In one transaction, convert held seats to sold and issue tickets.
