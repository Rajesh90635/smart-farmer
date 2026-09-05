# Case Routing

## Absolute rule: never random routing

`_try_auto_assign` in `case_service.py` always goes through
`nearby_professional_service.find_ranked_candidates`, which only ever
returns VERIFIED professionals (a hard filter at the repository query
level, not a post-hoc check). There is no code path in this phase that
assigns a case to a professional without going through this function.

## Routing inputs

| Input | Used? | Notes |
|---|---|---|
| Requested professional role (field_agent vs expert) | Yes | Farmer's explicit choice |
| Crop specialization | Yes | `_build_match_criteria` (case_service.py) resolves the case's crop_cycle -> crop_id |
| Disease category | No | Deliberately NOT populated - `AIAnalysis` has no category taxonomy, only a free-text `predicted_class`; guessing a category from that string would be a fabrication, not a real signal (see docs/audit/README.md's "Third pass" for the reasoning) |
| Farmer language | Yes | Resolved from the farmer's `FarmerProfile.preferred_language_code` |
| Service area | Yes | Resolved from the farm's `state_id`/`district_id` -> `State`/`District` name, matched against the professional's free-text `service_area` |
| Availability | Yes | AVAILABLE/BUSY scored; **OFFLINE is a hard exclusion**, not just a zero score (D34-01 - an OFFLINE professional can never be auto-assigned a new case) |
| Workload | Yes | Hard exclusion at max, scored otherwise |
| Reputation | Yes | Scored, capped contribution |

Disease category remains the one genuinely unpopulated field, and is
expected to stay that way until AIAnalysis (or a future model) carries a
real category-level signal - it is not a "next step," it is a boundary
against inventing a mapping that doesn't exist.

## Absolute rules fully enforced

- Only VERIFIED professionals are ever candidates.
- OFFLINE professionals are never candidates either, regardless of score.
- A declined professional is never re-offered the same case.
- Suspended/unverified professionals never receive cases.
- Workload limits are always respected.

## Trader/dealer routing

Not implemented this phase. The rule ("a trader/dealer must not
automatically receive crop disease photos") is trivially satisfied by
omission - no code path in this phase ever creates a CaseAssignment or
PhotoAccessGrant for a trader or dealer role. `_try_auto_assign` is only
ever called with role = field_agent or expert (enforced by
create_case's validation). Trader/dealer case routing is explicitly
future work (Prompt 9+), not silently half-built.
