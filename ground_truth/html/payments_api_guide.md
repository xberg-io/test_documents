# Payments API Guide

The Payments API lets you charge cards, issue refunds, and reconcile
settlements from a single REST surface. This guide covers
authentication, the core resources, and common error handling.

## Authentication

Every request must include a secret key in the `Authorization` header
using the `Bearer` scheme. Keys are environment-scoped: a key prefixed
with `sk_live_` operates on real funds, while `sk_test_` targets the
sandbox.

Rotate keys from the dashboard. **Never** embed a live key in
client-side code — treat it like a password.

## Core Resources

The API exposes three primary resources:

- **Charges** — a single attempt to move money from a customer.
- **Refunds** — a full or partial reversal of a settled charge.
- **Payouts** — a transfer of your available balance to a bank account.

Create a charge by POSTing an amount in the smallest currency unit. For
example, `1000` with currency `usd` means ten US dollars, not one
thousand.

## Endpoints

| Method | Path              | Purpose                         |
|--------|-------------------|---------------------------------|
| POST   | `/v1/charges`     | Create and confirm a charge     |
| GET    | `/v1/charges/:id` | Retrieve a charge by identifier |
| POST   | `/v1/refunds`     | Refund an existing charge       |
| GET    | `/v1/payouts`     | List settlement payouts         |

## Error Handling

Errors return a machine-readable `code` alongside a human `message`.
Retry only on `rate_limited` and `processing_error`; a `card_declined`
is *terminal* and must be surfaced to the buyer. Use idempotency keys so
a retried `POST` never double-charges a customer.
