"""
Area unit conversion. Per the Farm/Plot module rules: store a canonical
internal value (square meters) plus the farmer's original entered
value/unit for display — never silently convert and discard the original,
and never do ad-hoc conversion math scattered across the codebase.
"""
import enum
from decimal import Decimal


class AreaUnit(str, enum.Enum):
    ACRE = "acre"
    HECTARE = "hectare"
    GUNTA = "gunta"
    CENT = "cent"
    SQUARE_METER = "square_meter"


# Conversion factors to square meters. Gunta and cent are regionally
# common (Karnataka/Maharashtra and Kerala/Tamil Nadu respectively) but
# their exact definitions vary slightly by region/era - these are the
# commonly used approximations. Flagged here rather than silently assumed
# precise, since a legal/survey context would need the locally authoritative
# figure, not this one.
_TO_SQUARE_METERS: dict[AreaUnit, Decimal] = {
    AreaUnit.SQUARE_METER: Decimal("1"),
    AreaUnit.ACRE: Decimal("4046.8564224"),
    AreaUnit.HECTARE: Decimal("10000"),
    AreaUnit.GUNTA: Decimal("101.17"),
    AreaUnit.CENT: Decimal("40.4685642"),
}


def to_square_meters(value: Decimal, unit: AreaUnit) -> Decimal:
    if value <= 0:
        raise ValueError("Area value must be greater than zero.")
    return value * _TO_SQUARE_METERS[unit]


def from_square_meters(value_sqm: Decimal, target_unit: AreaUnit) -> Decimal:
    return value_sqm / _TO_SQUARE_METERS[target_unit]
