# Delivery Workflow

## Deliberately simple - no logistics platform

`Delivery` is a 1:1 companion to `Order` with just a status enum,
optional `estimated_delivery_date`, and free-text `tracking_note`. No
delivery-partner entity, no GPS, no route optimization - matching what
this platform can honestly support right now (Requirement 39's explicit
instruction not to over-build this).

## Statuses (exactly the 8 specified)

`PENDING`, `ASSIGNED`, `PICKED_UP`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`,
`DELIVERED`, `FAILED`, `RETURNED`. Updated by the dealer via
`PUT /dealer/orders/{id}/delivery` - there is no separate delivery-partner
role or account this phase; the dealer is responsible for reporting
delivery status themselves.

## "Estimated," never "Guaranteed"

`estimated_delivery_date` is the only delivery-timing field, and no
farmer-facing text in this phase's backend claims a guaranteed delivery
time - consistent with Requirement 42's explicit wording rule (this
project has no logistics data reliable enough to back a guarantee).

## Weather + delivery integration - not built this phase

`Delivery.weather_delay_note` exists as a column specifically so a future
integration with the Weather module (Prompt 7) can populate it ("Delivery
may be delayed due to severe weather") - but no code currently writes to
it. This is a disclosed gap, not a hidden claim of integration. Per
Requirement 51, even when built, this must remain informational only -
never an automatic order cancellation trigger.

## No delivery-partner entity yet

Requirement 40's future delivery-partner concept (verification, service
area, availability) is not modeled this phase - the dealer IS the
delivery reporter for now. When a distinct transporter role is needed,
it would follow the exact same `ProfessionalProfile` verification pattern
already established (Prompt 8), not a new verification system.

## Privacy

No delivery person's location (exact or approximate) is tracked or
exposed anywhere in this phase - there's no field for it. When live
tracking is eventually built, Requirement 41's rule (never expose exact
location unnecessarily) applies from day one of that design, not as an
afterthought.
