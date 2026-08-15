# Case Routing

## Absolute rule: never random routing

`_try_auto_assign` in `case_service.py` always goes through
`nearby_professional_service.find_ranked_candidates`, which only ever
returns VERIFIED professionals (a hard filter at the repository query
level, not a post-hoc check). There is no code path in this phase that
assigns a case to a professional without going through this function.

## Routing inputs (as implemented this phase)

| Input | Used? | Notes |
|---|---|---|
| Requested professional role (field_agent vs expert) | Yes | Farmer's explicit choice |
| Crop specialization | Partial | Scored in the matching algorithm, but not currently populated from the case context - see limitation below |
| Disease category | Partial | Same as above |
| Farmer language | No | Not wired into MatchCriteria from case creation this phase |
| Service area | No | Not wired from the farm's location this phase |
| Availability | Yes | Scored |
| Workload | Yes | Hard exclusion at max, scored otherwise |
| Reputation | Yes | Scored, capped contribution |

## Known limitation, disclosed plainly

`_try_auto_assign` currently only passes `role` and
`exclude_professional_ids` to `MatchCriteria` - crop, disease category,
language, and service area are NOT populated from the case's actual
context (crop cycle's crop, farmer's language, farm's district) even
though the matching algorithm and data model both support all of them.
This means the routing (finding SOME verified professional of the right
role) works and is tested, but the "smart" part of the routing example
(crop + language + service-area combined routing) is not fully connected
yet.

Why this is disclosed rather than silently shipped as "done": the
underlying matching algorithm was built and tested in isolation
(nearby_professional_service tests pass with crop/language/area
criteria), but wiring case_service.create_case to actually populate those
criteria from the case's farmer/crop/farm context was not completed in
this pass - a straightforward next step, not a redesign.

## Absolute rules still fully enforced regardless of the above gap

- Only VERIFIED professionals are ever candidates - unaffected by which
  criteria are populated.
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
