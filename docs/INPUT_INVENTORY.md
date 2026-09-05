# Input Inventory

## Entity: InputInventoryItem

The farmer's OWN on-farm stock of a seed/fertilizer/crop-protection/
bio-input - entirely separate from `DealerProduct.stock_quantity` (the
dealer's sellable stock, decremented at checkout) and `OrderItem.quantity`
(what was ordered, not what's currently held). Confirmed missing by
exhaustive search before this phase (docs/audit/c04_inputs.md, Domains
21-24) - no such model existed anywhere.

`category` reuses `Product.category`'s vocabulary but is stored as a
plain string, not a shared native Postgres enum with `products.category` -
avoids altering that existing enum type.

## Creation

Manual only this phase - the farmer records what they hold via
`POST /input-inventory` (optionally linked to a catalog `Product` via
`product_id`, or a free-text `custom_name` when not tied to the catalog -
one of the two is required). Auto-creating an inventory row when a
marketplace order is delivered is a reasonable future enhancement using
the same `create_item`/`restock` functions - not built this phase.

## Lifecycle

```
Create (initial quantity)
   |
   +-- Usage recorded (POST .../usage) -> quantity decreases
   |        |
   |        +-- crosses low_stock_threshold -> STOCK_ALERT notification (once per episode)
   |
   +-- Restock (POST .../restock) -> quantity increases
   |        |
   |        +-- back above threshold -> low-stock alert gate clears (re-arms for next time)
   |
   +-- Correction (POST .../correct) -> quantity set directly, reason required, audited
```

## Low-stock alert (D22-06/D24-08)

Fires the first time `quantity <= low_stock_threshold` (a farmer-set,
optional value - no threshold means no low-stock alerts for that item).
Gated by `low_stock_alerted_at` (not just the Notification table's own
dedup_key) so repeated usage calls while still low don't spam a second
alert, but restocking above the threshold and dropping low again
correctly re-alerts. Verified by
`tests/test_input_inventory.py::test_low_stock_alert_fires_once_then_stays_quiet_until_restocked`.

## Expiry warning (D24-09)

Proactive, not farmer-screen-triggered: `app/services/scheduler.py` runs
`input_inventory_service.run_expiry_check_sweep` every
`input_inventory_expiry_sweep_interval_seconds` (default hourly),
alerting once per item within `input_expiry_warning_days` (default 14)
of `expiry_date`, gated by `expiry_alerted_at`. Skips items with
`quantity <= 0` (nothing left to warn about using). Disabled in the
`testing` environment like the Expert SLA sweep - tests call
`run_expiry_check_sweep` directly.

## Notifications

New `NotificationCategory.STOCK_ALERT` (migration `fb6859bdd48d` adds the
Postgres enum value), mapped to `general_notifications_enabled` in
`notification_service._CATEGORY_PREFERENCE_MAP` (same bucket as
`HARVEST_ALERT` - not safety-critical enough to warrant its own
preference toggle). Message keys `INPUT_LOW_STOCK`/`INPUT_EXPIRY_WARNING`
are English-only this phase, consistent with this project's other
non-`daily_summary_*` message-key families pending native-speaker review.

## Explicitly not built this phase

- **Authenticity verification** (D26-04): no QR/barcode/manufacturer
  database cross-check exists anywhere in this project
  (`docs/PROMPT9_ASSUMPTIONS_RISKS.md:80-89` already discloses this) - a
  real authenticity claim requires a real manufacturer/registry
  integration this project does not fabricate. Remains MISSING, not
  something this phase attempted to fake.
- **Automatic purchase -> stock increase**: inventory creation/restock is
  farmer-initiated only; no code path links a completed marketplace order
  to an automatic inventory entry.

## Ownership

Every item lookup is scoped to `farmer_id` on the row itself - cross-farmer
access returns 404, verified by test.
