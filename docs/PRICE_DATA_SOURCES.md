# Price Data Sources

## No live external price feed is integrated

Every `ReferencePrice` row in this phase's seed data (and every one
created via `POST /products/{id}/reference-prices`) is entered manually
via `ADMIN_ENTERED_REFERENCE` - there is no integration with any external
agricultural commodity/input price API. This is consistent with the
"no fake market price" absolute rule: rather than fabricate a connection
to a data source that doesn't exist, this phase makes admin entry the
only real path and requires every row to declare its source type
honestly.

## Source types supported (the schema is ready, only one is used in practice)

| Source type | Used this phase? |
|---|---|
| OFFICIAL_SOURCE | No - would require integration with a government agricultural price portal |
| AUTHORIZED_MARKET_SOURCE | No - would require integration with a mandi/market price API |
| MANUFACTURER_REFERENCE | No - would require a manufacturer data-sharing agreement |
| VERIFIED_MARKET_DATA | No - would require a licensed market data provider |
| ADMIN_ENTERED_REFERENCE | **Yes - the only source type actually used** |

## What a real integration would require (documented per the free-first rule)

| Service | Purpose | Free option | Limitations | Expected cost | When required |
|---|---|---|---|---|---|
| A government mandi price API (e.g. Agmarknet, data.gov.in agricultural datasets) | Real market reference prices for commodities | Agmarknet/data.gov.in APIs are free/public | Coverage is commodity-focused (grains, vegetables), not branded agricultural inputs like fertilizers/pesticides - would need to be supplemented with manufacturer/dealer-network data for those categories; data freshness/API reliability not yet verified from this environment | Free for the public APIs themselves; engineering time to integrate | Only when real reference prices for real products are needed - not required for continued backend development |
| A manufacturer/industry price-reporting agreement | Reference prices for branded crop-protection/fertilizer products specifically | None free - typically requires a direct relationship | Requires business development effort, not just engineering | Varies, likely relationship-based rather than a fixed fee | Same as above |

## Staleness is always visible, never hidden

Every `ReferencePrice` carries `effective_date` and `retrieved_at` in the
API response - a consuming client can always tell how old the data is.
The friendly "updated X days ago" rendering itself is not yet built
server-side (see docs/PRICE_TRANSPARENCY.md's disclosed gap) but the raw
data needed to build it is already there.
