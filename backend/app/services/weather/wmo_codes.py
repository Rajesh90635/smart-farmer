"""
D15-05/D15-07 (docs/audit/FINAL_CANONICAL_group_A.md): condition_code
stores the raw WMO ("WW") weather-interpretation code exactly as returned
by the weather provider (Open-Meteo uses this same public, standardized
table - not a code this project invented). This module decodes ONLY the
two categories these scenarios actually ask for - storm and hail - both
real, well-defined subsets of the published table:

  95       Thunderstorm, slight or moderate
  96       Thunderstorm with slight hail
  99       Thunderstorm with heavy hail

Deliberately NOT attempted here: D15-06 (cyclone). A cyclone is a
large-scale system, not a point-in-time WMO condition code - no code in
this table represents it, and inventing one would be exactly the kind of
fabricated classification this project's own anti-fabrication rule
forbids. Real cyclone detection needs a track/warning feed (see D75-05,
docs/audit/FINAL_CANONICAL_group_D.md), which does not exist in this
project.
"""

_STORM_CODES = {"95", "96", "99"}
_HAIL_CODES = {"96", "99"}


class ConditionClassification:
    __slots__ = ("is_storm", "is_hail")

    def __init__(self, is_storm: bool | None, is_hail: bool | None) -> None:
        self.is_storm = is_storm
        self.is_hail = is_hail


def classify_condition_code(condition_code: str | None) -> ConditionClassification:
    """None (never a fabricated False) when condition_code itself is
    unknown/unavailable - honestly distinct from "known, and not a
    storm/hail condition"."""
    if condition_code is None:
        return ConditionClassification(is_storm=None, is_hail=None)
    return ConditionClassification(
        is_storm=condition_code in _STORM_CODES,
        is_hail=condition_code in _HAIL_CODES,
    )
