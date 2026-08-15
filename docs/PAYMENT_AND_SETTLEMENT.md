# Payment and Settlement (Harvest Sales)

## Fully reuses Prompt 9's sandbox Payment - no second payment system

`sale_order_service.py` creates `Payment` rows in the EXACT same table
Prompt 9 built, using the new `sale_order_id` column (with `order_id`
left NULL) instead of duplicating a `SalePayment` table. The provider is
always `SANDBOX` - no real gateway integration exists for harvest sales,
same as for agricultural input purchases. See docs/PAYMENT_ARCHITECTURE.md
(Prompt 9) for the full sandbox architecture, which applies unchanged
here.

## The buyer pays the farmer - direction matters, mechanism doesn't change

Conceptually the payment direction is reversed from Prompt 9 (buyer pays
farmer, not farmer pays dealer), but the `Payment` table has no
"direction" concept at all - it's just `sale_order_id` + `amount` +
`status`. The direction is implicit in which parties are on the
`SaleOrder` (`farmer_id` = recipient, `buyer_id` = payer) - no schema
change was needed to support the reversed flow.

## Settlement fee model - not configured, disclosed honestly

`SaleOrder.charges` is always `0` this phase - there is no platform
commission, transportation-fee calculation, or collection-fee model
implemented. Requirement 57's "if the platform eventually charges
commission, show it clearly" is trivially satisfied by having nowhere to
hide a fee (the field is a real, separate column, always visible), but
no actual fee is charged or computed yet. When a real fee model exists,
it populates this same field - no schema change needed.

## Never marks a sale PAID without real confirmation

`sale_order_service.complete_payment()` only transitions the sale to
`PAID` when `succeed=True` is explicitly passed to the TEST-ONLY sandbox
completion endpoint - mirroring Prompt 9's exact payment-honesty pattern.
A `succeed=False` call correctly leaves the sale in `PAYMENT_PENDING`,
never `PAID` - the same guarantee already verified for input-purchase
orders, now verified again for harvest sales via the full lifecycle test.

## What a real settlement system would require (free vs. paid, per Requirement 76)

| Service | Purpose | Free option | Limitations | Expected cost | When required |
|---|---|---|---|---|---|
| A real payment gateway (same as Prompt 9's assessment) | Actually move money from buyer to farmer | Sandbox/test modes are free | Cannot process real transactions; production requires KYC | Percentage-based fees | Only once real harvest sales with real money go live |
| A payout/disbursement mechanism to farmers | Getting money from the platform's collection account to individual farmer bank accounts/UPI | Most gateways bundle this (e.g. Razorpay Route) | Still requires KYC/compliance, and a farmer's bank/UPI details would need secure capture (not built - no such field exists anywhere in this codebase) | Included in gateway fees typically | Same as above |
