"""
Role constants matching the RBAC model in the approved architecture.
This module defines the *vocabulary* only — assignment workflows and the
full permission matrix are a later module, not part of this foundation.
"""
from enum import StrEnum


class Role(StrEnum):
    FARMER = "farmer"
    FAMILY_MEMBER = "family_member"
    FARM_WORKER = "farm_worker"
    FIELD_AGENT = "field_agent"
    # Renamed from AGRONOMIST -> EXPERT to match the exact role vocabulary
    # given in the Auth/Farmer-profile spec ("FARMER, FIELD_AGENT, EXPERT,
    # DEALER, BUYER, ADMIN"). Safe rename - nothing else in the codebase
    # referenced AGRONOMIST yet. This is the SAME role the Professional
    # Network phase calls "AGRICULTURE_EXPERT" - reused, not recreated.
    EXPERT = "expert"
    DEALER = "dealer"
    BUYER = "buyer"
    TRANSPORTER = "transporter"
    LAB = "lab"
    ADMIN = "admin"

    # Added in the Professional Network phase - no equivalent existed yet.
    TRADER = "trader"

    # The AI/Automation actor. Deliberately never granted financial-write
    # authority anywhere in the system — enforced at the dependency/policy
    # level wherever this role is checked, not just by convention.
    AUTOMATION_SERVICE = "automation_service"


# Roles seeded into the `roles` DB table in this phase (see the
# create_auth_and_farmer_tables migration). FAMILY_MEMBER, FARM_WORKER,
# TRANSPORTER, LAB, and AUTOMATION_SERVICE remain valid vocabulary but have
# no DB row yet - they're seeded when their owning module needs them.
SEEDED_ROLE_CODES: tuple[Role, ...] = (
    Role.FARMER,
    Role.FIELD_AGENT,
    Role.EXPERT,
    Role.DEALER,
    Role.BUYER,
    Role.ADMIN,
    Role.TRADER,
)
