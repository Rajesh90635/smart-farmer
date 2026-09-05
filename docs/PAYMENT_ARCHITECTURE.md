# Payment Architecture

## Provider abstraction (D90-10)

`app/services/payment/payment_gateway_provider.py` - the same "real
business logic depends on an interface, not a specific vendor" pattern
already used for `WeatherProvider`/`ModelProvider`. Named
`PaymentGatewayProvider`, not `PaymentProvider` - that name is already
`app.models.payment.PaymentProvider`, the DB enum recording which
provider a `Payment` row used (SANDBOX/UPI/CARD/NET_BANKING/CASH_ON_DELIVERY).

**Still SANDBOX ONLY - the abstraction doesn't change that.**
`SandboxPaymentGatewayProvider` is the only adapter actually implemented;
`Settings.payment_gateway_provider` (default `"sandbox"`) is the one
switch point - naming a real gateway with no adapter class falls back to
`NotConfiguredPaymentGatewayProvider` (always `available=False`, never a
fabricated reference), the same fail-honest pattern as
`NotConfiguredWeatherProvider`/the SMS provider dependency. `UPI`, `CARD`,
`NET_BANKING`, `CASH_ON_DELIVERY` remain enum-only documented future
surface, not working integrations.

`PaymentGatewayProvider.is_sandbox_completable` is the structural guard:
only a provider whose completion can legitimately be driven by a direct,
synchronous, farmer-callable call reports `True`. A real gateway adapter
must report `False`, and `payment_service.complete_payment`/
`sale_order_service.complete_payment` now REFUSE to run at all (409) when
the configured provider isn't sandbox-completable - not a new business
rule, just moving the same "this must be replaced before real money is
involved" guarantee from documentation-only into code that would
actually stop a misconfigured production deployment.

## The flow as built

```
POST /orders/{id}/pay
   -> payment_gateway_provider.initiate_payment(...) - real amount, provider decides the reference
   -> unavailable -> 503, order never enters PAYMENT_PENDING (no fake payment state)
   -> available   -> Order: PAYMENT_PENDING, Payment row created: PENDING, provider-issued external_reference

POST /orders/{id}/pay/complete   <- TEST-ONLY, refused (409) unless is_sandbox_completable
   -> simulates what a real gateway's webhook would report
   -> succeed=true  -> Payment: SUCCESS, Order: PAID
   -> succeed=false -> Payment: FAILED, Order stays PAYMENT_PENDING (never PAID)
```

Verified by test that a failed payment genuinely leaves the order
un-paid (`test_payment_failure_does_not_mark_order_paid`) - there is no
code path that marks an order `PAID` without a `Payment` row actually
reaching `SUCCESS` status first. The marketplace-sale payment path
(`sale_order_service.py`, `/marketplace/purchases/{id}/pay...`) goes
through the exact same `PaymentGatewayProvider` interface.

## `POST .../pay/complete` is a sandbox test hook, not a production endpoint

A real deployment would replace the sandbox adapter with a real gateway
adapter (Razorpay, PayU, etc. - none integrated here) plus a webhook
receiver that THE GATEWAY calls, not the farmer's own client -
`is_sandbox_completable=False` on that adapter is what makes shipping
this test hook to production impossible to trigger for a real gateway,
not just a documentation warning. Flagged here so it isn't mistaken for
a finished payment integration.

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
