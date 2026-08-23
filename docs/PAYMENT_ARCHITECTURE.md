# Payment Architecture

## SANDBOX ONLY this phase - stated plainly

No real payment gateway is integrated. `PaymentProvider.SANDBOX` is the
only value ever actually used by `payment_service.py`; `UPI`, `CARD`,
`NET_BANKING`, `CASH_ON_DELIVERY` exist in the enum as the abstraction's
documented future surface, not as working integrations.

## The flow as built

```
POST /orders/{id}/pay
   -> Order: PAYMENT_PENDING
   -> Payment row created: PENDING, provider=SANDBOX, a fake external_reference

POST /orders/{id}/pay/complete   <- TEST-ONLY, see below
   -> simulates what a real gateway's webhook would report
   -> succeed=true  -> Payment: SUCCESS, Order: PAID
   -> succeed=false -> Payment: FAILED, Order stays PAYMENT_PENDING (never PAID)
```

Verified by test that a failed payment genuinely leaves the order
un-paid (`test_payment_failure_does_not_mark_order_paid`) - there is no
code path that marks an order `PAID` without a `Payment` row actually
reaching `SUCCESS` status first.

## `POST /orders/{id}/pay/complete` is a sandbox test hook, not a production endpoint

A real deployment would replace this with a webhook receiver from an
actual gateway (Razorpay, PayU, etc. - none integrated here) that the
gateway calls, not the farmer's own client. Shipping this endpoint to
production as-is would let a farmer mark their own payment successful
without actually paying - **this must be replaced, not merely left in
place, before any real money is involved.** Flagged explicitly here so it
isn't mistaken for a finished payment integration.

## Payment security - structurally enforced, not just policy

The `Payment` model has **no columns** for card number, CVV, UPI PIN, or
banking password - it is not possible to accidentally store one, because
there is nowhere to put it. `external_reference` is a sandbox-generated
opaque string, never real payment instrument data.

## When a real gateway is needed (documented per the free-first requirement)

| Service | Purpose | Free option | Limitations | Expected cost | When required |
|---|---|---|---|---|---|
| A real payment gateway (e.g. Razorpay, PayU, Cashfree) | Actually move money for a real order | Most Indian gateways offer a sandbox/test mode free of charge for development | Sandbox mode cannot process real transactions; production requires KYC/business registration with the gateway | Percentage-based transaction fees (varies by gateway, typically 1-2%) plus possible setup/compliance costs | Only once real orders with real money are going live - not needed for continued backend development |

No paid service was silently introduced this phase - the entire payment
layer is free (PostgreSQL + application code), consistent with
Requirement 70.
