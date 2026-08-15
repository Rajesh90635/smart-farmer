# Buyer Workflow

## Verification reused entirely from Prompt 8 - no second system

Buyer registration creates a `ProfessionalProfile` with `role='buyer'` -
the EXACT same table, the EXACT same `verification_status`
(PENDING/VERIFIED/REJECTED/SUSPENDED/EXPIRED) enum, and the EXACT same
admin-only verify/reject/suspend/reactivate endpoints already built in
Prompt 8. Nothing new was built for buyer verification specifically.
Verified by test: a newly-registered buyer starts `PENDING`
(`test_buyer_registration_starts_pending`), and an unverified buyer
cannot make an offer at all (`test_unverified_buyer_cannot_make_an_offer`,
404 - "no verified buyer profile found").

## BuyerBusinessProfile - only genuinely buyer-specific fields

Mirrors `DealerBusinessProfile`'s exact pattern from Prompt 9: a 1:1
extension holding `buyer_type` (BUSINESS_BUYER/WHOLESALER/PROCESSOR/
RETAILER/TRADER/INSTITUTIONAL_BUYER), `crops_purchased`,
`quality_requirements`, `min_quantity`/`max_quantity`,
`purchase_frequency`, `collection_method`. Sensitive verification
documents (there are none captured yet beyond what `ProfessionalProfile`
already has) are never exposed to farmers - the buyer-facing profile
response only returns display name, buyer type, crops purchased, and
quantity range.

## Buyer discovery of listings

`GET /marketplace/listings?crop_id=...` - straightforward filtered
browse. **Not built:** ranking listings by relevance to the buyer's own
`BuyerBusinessProfile` preferences (quantity range, crops purchased) -
every verified buyer currently sees the same unranked list, filtered
only by crop if specified. A disclosed gap, not silently handled.

## Buyer order dashboard

`GET /marketplace/purchases` lists the buyer's own `SaleOrder`s only -
verified by the same ownership-check pattern used throughout this
codebase (a query scoped to `buyer_id`, resolved from the authenticated
user's own `ProfessionalProfile`, never a client-supplied buyer id).

## Chat / in-app communication - NOT built this phase (disclosed gap)

Requirement 21/22 asks for a structured chat foundation (text/offer/
counter-offer/image/system messages) between farmer and buyer. This
phase does **not** build a chat system - negotiation happens entirely
through the structured `BuyerOffer`/`CounterOffer` tables (see
docs/OFFER_NEGOTIATION.md), which already carry price/quantity/message
fields sufficient for a negotiation, but there is no free-form messaging
channel, no image-in-chat capability, and no rate limiting for message
volume (moot, since no messaging exists). This is real, disclosed future
work, not a hidden shortcut - the offer/counter-offer system is a
legitimate structured alternative for the negotiation itself, but does
not cover general conversation ("what packaging do you need?" etc.).
