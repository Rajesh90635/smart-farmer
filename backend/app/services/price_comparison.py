"""
Price comparison / Scam Shield. Pure functions - no I/O - so they're
fully unit-testable without a database or live market feed.

HARD RULES:
- Never accuses a dealer of fraud - only reports a factual price
  comparison and a neutral flag level (HIGH/UNUSUAL/REVIEW_REQUIRED).
- Never normalizes across incompatible units (ml vs kg) - comparison is
  only ever performed between products with the same pack_size_unit.
- Every anomaly comparison shows its basis (the actual reference price
  used) - never a bare "this seems high" with no evidence.
"""
from dataclasses import dataclass
from decimal import Decimal

from app.core.config import Settings
from app.models.price_anomaly_flag import PriceAnomalyLevel


@dataclass(frozen=True)
class PriceComparisonResult:
    dealer_price: Decimal
    price_per_unit: Decimal
    unit: str
    reference_price: Decimal | None
    reference_price_per_unit: Decimal | None
    percent_above_reference: float | None
    anomaly_level: PriceAnomalyLevel | None


def price_per_unit(price: Decimal, pack_size_value: Decimal) -> Decimal:
    if pack_size_value <= 0:
        raise ValueError("pack_size_value must be greater than zero.")
    # Quantized to money's own standard 2 decimal places (matches every
    # price/amount column in this app, all Numeric(x, 2)) - plain Decimal
    # division here can otherwise return an exact-but-scientific-notation
    # result (e.g. Decimal("250.00") / Decimal("1.000") == Decimal("2.5E+2")),
    # which serializes to JSON as the literal string "2.5E+2" and would
    # render as garbage in a farmer-facing price display.
    return (price / pack_size_value).quantize(Decimal("0.01"))


def compare_price(
    *,
    dealer_price: Decimal,
    pack_size_value: Decimal,
    pack_size_unit: str,
    reference_price: Decimal | None,
    reference_pack_size_value: Decimal | None,
    settings: Settings,
) -> PriceComparisonResult:
    dealer_per_unit = price_per_unit(dealer_price, pack_size_value)

    if reference_price is None or reference_pack_size_value is None:
        return PriceComparisonResult(
            dealer_price=dealer_price,
            price_per_unit=dealer_per_unit,
            unit=pack_size_unit,
            reference_price=None,
            reference_price_per_unit=None,
            percent_above_reference=None,
            anomaly_level=None,
        )

    reference_per_unit = price_per_unit(reference_price, reference_pack_size_value)
    percent_above = float((dealer_per_unit - reference_per_unit) / reference_per_unit * 100) if reference_per_unit > 0 else None

    level = None
    if percent_above is not None:
        if percent_above >= settings.price_anomaly_review_percent:
            level = PriceAnomalyLevel.REVIEW_REQUIRED
        elif percent_above >= settings.price_anomaly_unusual_percent:
            level = PriceAnomalyLevel.UNUSUAL
        elif percent_above >= settings.price_anomaly_high_percent:
            level = PriceAnomalyLevel.HIGH

    return PriceComparisonResult(
        dealer_price=dealer_price,
        price_per_unit=dealer_per_unit,
        unit=pack_size_unit,
        reference_price=reference_price,
        reference_price_per_unit=reference_per_unit,
        percent_above_reference=percent_above,
        anomaly_level=level,
    )
