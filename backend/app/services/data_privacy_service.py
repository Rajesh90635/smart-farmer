"""
Data export & account deletion (D100-09, docs/audit/c13_governance_farmbrain_security.md).

SCOPING DISCLOSURE (read before trusting this as legal compliance):
This is a good-faith, MVP-scope implementation of "give a farmer their
data" and "let a farmer ask to stop being tracked" - it is NOT a
certified DPDP Act / GDPR compliance review, and none of the choices
below (what counts as "PII", what gets retained vs. scrubbed, that
deactivation is soft rather than a hard delete) have had real legal
sign-off. Treat this as the technical foundation a real compliance pass
would refine, not the final word.

## Export scope

Covers the farmer-facing data this project actually has a repository
query for: profile, consents, farms/plots, crop cycles and everything
scoped to them (tasks, treatments + follow-ups, AI analyses, crop-photo
METADATA), harvests + listings, expert cases, dealer orders, marketplace
sales, notifications, input inventory, cost estimates, invoices, and
ledger entries.

Explicitly NOT included, disclosed rather than silently omitted:
- Raw photo/image file bytes (only metadata - filename, dimensions,
  quality flags, GPS if provided). The files themselves are reachable
  via the existing authenticated `/crop-photos/{id}/file` endpoint one at
  a time, not bundled into this export.
- `AuditLog` rows - an internal system record of actions taken, not
  itself "the farmer's data" the same way a Farm or CropCycle row is;
  also never modified per this project's own append-only convention.
- Other parties' data referenced by ID only (a buyer's own business
  profile, a professional's own profile, a dealer's product catalog) -
  this export is scoped to what THIS farmer owns, not everyone who ever
  interacted with them.

## Deletion scope

`request_account_deletion` does NOT hard-delete the account or cascade-
delete Farm/Order/SaleOrder/Payment/Notification rows - financial and
transactional records commonly have real retention obligations (tax,
dispute resolution, audit) this codebase has no authority to just erase
on its own judgment. Instead:
- `User.status` -> INACTIVE (the existing, previously-unwired
  `AccountStatus` enum - confirmed unused anywhere before this).
- Direct PII is scrubbed: `phone_number` replaced with a non-functional
  placeholder (must stay unique), `email` cleared, `FarmerProfile.full_name`
  replaced with a generic placeholder.
- Every active `RefreshToken` is revoked (the farmer is logged out
  everywhere on next refresh).
- Audited (`ACCOUNT_DELETION_REQUESTED`), same append-only AuditLog every
  other action in this project uses.

KNOWN LIMITATION, disclosed: `current_user.py`'s access-token check
validates only the JWT signature/expiry/role claim, never `User.status`
against the database (true for every account status, not something this
change introduces) - an already-issued access token keeps working for up
to `jwt_access_token_minutes` (15 by default) after deletion is
requested. Refresh tokens ARE revoked immediately, so this is a bounded
window, not indefinite continued access - closing it fully would need a
token blocklist, a bigger change to this project's stateless-JWT design
than this task should make unilaterally.
Everything else the farmer owns (farms, crop cycles, harvests, orders,
sales, notifications, etc.) is RETAINED, now associated with an
anonymized account rather than a real phone number/name - a defensible,
common "right to erasure with retention exceptions" pattern, not
something this implementation claims is definitely what DPDP/GDPR
requires for this specific business.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ai_analysis import AIAnalysis
from app.models.crop_photo import CropPhoto
from app.models.harvest_listing import HarvestListing
from app.models.harvest_record import HarvestRecord
from app.models.order import Order
from app.models.sale_order import SaleOrder
from app.models.task import Task
from app.models.treatment_follow_up import TreatmentFollowUp
from app.models.treatment_record import TreatmentRecord
from app.models.user import AccountStatus, User
from app.repositories import (
    ai_analysis_repository,
    case_repository,
    crop_cost_estimate_repository,
    crop_cycle_repository,
    crop_photo_repository,
    farm_repository,
    harvest_repository,
    invoice_repository,
    ledger_entry_repository,
    notification_repository,
    order_repository,
    plot_repository,
    refresh_token_repository,
    sale_order_repository,
    task_repository,
    treatment_repository,
)
from app.services import consent_service, input_inventory_service
from app.services.audit_logger import AuditLogger

_ALL = 100_000  # a pragmatic "no real farmer exceeds this" page size for reusing paginated repo queries unpaginated


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _dec(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def export_my_data(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    user = db.get(User, farmer_uuid)
    if user is None:
        raise AppError(error_codes.NOT_FOUND, "Account not found.", 404)

    farms = farm_repository.list_for_farmer(db, farmer_uuid, limit=_ALL, offset=0)[0]
    plots = [p for farm in farms for p in plot_repository.list_for_farm(db, farm.id, limit=_ALL, offset=0)[0]]
    crop_cycles = crop_cycle_repository.list_all_for_farmer(db, farmer_uuid)

    tasks: list[Task] = []
    treatments: list[TreatmentRecord] = []
    follow_ups: list[TreatmentFollowUp] = []
    analyses: list[AIAnalysis] = []
    photos: list[CropPhoto] = []
    cost_estimates = []
    invoices = []
    ledger_entries = []
    for cc in crop_cycles:
        tasks.extend(task_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))
        cc_treatments = treatment_repository.list_treatments_for_crop_cycle(db, cc.id, farmer_uuid)
        treatments.extend(cc_treatments)
        for t in cc_treatments:
            follow_ups.extend(treatment_repository.list_follow_ups_for_treatment(db, t.id, farmer_uuid))
        analyses.extend(ai_analysis_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))
        photos.extend(crop_photo_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))
        cost_estimates.extend(crop_cost_estimate_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))
        invoices.extend(invoice_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))
        ledger_entries.extend(ledger_entry_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))

    harvests: list[HarvestRecord] = harvest_repository.list_harvests_for_farmer(db, farmer_uuid, limit=_ALL, offset=0)[0]
    listings: list[HarvestListing] = harvest_repository.list_listings_for_farmer(db, farmer_uuid, limit=_ALL, offset=0)[0]
    cases = case_repository.list_cases_for_farmer(db, farmer_uuid, limit=_ALL, offset=0)[0]
    orders: list[Order] = order_repository.list_orders_for_farmer(db, farmer_uuid, limit=_ALL, offset=0)[0]
    sales: list[SaleOrder] = sale_order_repository.list_sales_for_farmer(db, farmer_uuid, limit=_ALL, offset=0)[0]
    notifications = notification_repository.list_for_farmer(db, farmer_uuid, unread_only=False, limit=_ALL, offset=0)[0]
    inventory = input_inventory_service.list_items(db, farmer_id)

    return {
        "exported_at": _iso(datetime.now(timezone.utc)),
        "profile": {
            "user_id": str(user.id),
            "phone_number": user.phone_number,
            "email": user.email,
            "account_status": user.status.value,
            "full_name": user.farmer_profile.full_name if user.farmer_profile else None,
            "preferred_language_code": user.farmer_profile.preferred_language_code if user.farmer_profile else None,
            "created_at": _iso(user.created_at),
        },
        "consents": [c.model_dump(mode="json") for c in consent_service.list_consents(db, farmer_id)],
        "farms": [
            {
                "id": str(f.id), "farm_name": f.farm_name, "latitude": _dec(f.latitude), "longitude": _dec(f.longitude),
                "area_value": _dec(f.area_value), "area_unit": f.area_unit.value, "status": f.status.value,
                "created_at": _iso(f.created_at),
            }
            for f in farms
        ],
        "plots": [
            {
                "id": str(p.id), "farm_id": str(p.farm_id), "plot_name": p.plot_name, "area_value": _dec(p.area_value),
                "soil_type": p.soil_type, "irrigation_type": p.irrigation_type, "created_at": _iso(p.created_at),
            }
            for p in plots
        ],
        "crop_cycles": [
            {
                "id": str(cc.id), "plot_id": str(cc.plot_id), "crop_id": str(cc.crop_id),
                "sowing_date": cc.sowing_date.isoformat() if cc.sowing_date else None,
                "cultivation_status": cc.cultivation_status.value, "failure_reason": cc.failure_reason,
                "created_at": _iso(cc.created_at),
            }
            for cc in crop_cycles
        ],
        "tasks": [
            {
                "id": str(t.id), "crop_cycle_id": str(t.crop_cycle_id), "title": t.title, "status": t.status.value,
                "due_date": t.due_date.isoformat() if t.due_date else None, "created_at": _iso(t.created_at),
            }
            for t in tasks
        ],
        "treatments": [
            {
                "id": str(t.id), "crop_cycle_id": str(t.crop_cycle_id), "application_date": t.application_date.isoformat(),
                "notes": t.notes, "created_at": _iso(t.created_at),
            }
            for t in treatments
        ],
        "treatment_follow_ups": [
            {
                "id": str(f.id), "treatment_id": str(f.treatment_id), "observation_date": f.observation_date.isoformat(),
                "notes": f.notes,
            }
            for f in follow_ups
        ],
        "ai_analyses": [
            {
                "id": str(a.id), "crop_photo_id": str(a.crop_photo_id), "predicted_class": a.predicted_class,
                "confidence": a.confidence, "result_status": a.result_status.value,
                "farmer_correction": a.farmer_correction, "farmer_correction_notes": a.farmer_correction_notes,
                "created_at": _iso(a.created_at),
            }
            for a in analyses
        ],
        "crop_photos_metadata": [
            {
                "id": str(p.id), "crop_cycle_id": str(p.crop_cycle_id), "original_filename": p.original_filename,
                "upload_timestamp": _iso(p.upload_timestamp), "latitude": _dec(p.latitude), "longitude": _dec(p.longitude),
                "upload_status": p.upload_status.value,
            }
            for p in photos
        ],
        "harvests": [
            {
                "id": str(h.id), "crop_cycle_id": str(h.crop_cycle_id), "status": h.status.value,
                "estimated_quantity": _dec(h.estimated_quantity), "actual_quantity": _dec(h.actual_quantity),
                "actual_harvest_date": h.actual_harvest_date.isoformat() if h.actual_harvest_date else None,
            }
            for h in harvests
        ],
        "harvest_listings": [
            {
                "id": str(listing.id), "harvest_record_id": str(listing.harvest_record_id),
                "quantity_available": _dec(listing.quantity_available), "unit": listing.unit,
                "preferred_price": _dec(listing.preferred_price), "created_at": _iso(listing.created_at),
            }
            for listing in listings
        ],
        "expert_cases": [
            {
                "id": str(c.id), "crop_cycle_id": str(c.crop_cycle_id), "reason": c.reason.value, "status": c.status.value,
                "final_verified_class": c.final_verified_class, "created_at": _iso(c.created_at),
            }
            for c in cases
        ],
        "dealer_orders": [
            {
                "id": str(o.id), "dealer_id": str(o.dealer_id), "status": o.status.value,
                "final_amount": _dec(o.final_amount), "created_at": _iso(o.created_at),
            }
            for o in orders
        ],
        "marketplace_sales": [
            {
                "id": str(s.id), "harvest_listing_id": str(s.harvest_listing_id), "buyer_id": str(s.buyer_id),
                "quantity": _dec(s.quantity), "net_value": _dec(s.net_value), "status": s.status.value,
                "created_at": _iso(s.created_at),
            }
            for s in sales
        ],
        "notifications": [
            {
                "id": str(n.id), "category": n.category.value, "priority": n.priority.value, "title": n.title,
                "body": n.body, "read_at": _iso(n.read_at), "created_at": _iso(n.created_at),
            }
            for n in notifications
        ],
        "input_inventory": [item.model_dump(mode="json") for item in inventory.items],
        "cost_estimates": [
            {
                "id": str(e.id), "crop_cycle_id": str(e.crop_cycle_id), "category": e.category,
                "estimated_amount": _dec(e.estimated_amount),
            }
            for e in cost_estimates
        ],
        "invoices": [
            {
                "id": str(i.id), "crop_cycle_id": str(i.crop_cycle_id),
                "vendor_name": i.confirmed_vendor_name or i.extracted_vendor_name,
                "amount": _dec(i.confirmed_amount if i.confirmed_amount is not None else i.extracted_amount),
            }
            for i in invoices
        ],
        "ledger_entries": [
            {
                "id": str(e.id), "crop_cycle_id": str(e.crop_cycle_id), "entry_type": e.entry_type.value,
                "category": e.category.value, "amount": _dec(e.amount), "entry_date": e.entry_date.isoformat(),
            }
            for e in ledger_entries
        ],
        "not_included": [
            "Raw photo/video file bytes (metadata only - files remain reachable one at a time via the existing authenticated file endpoint)",
            "Internal audit log entries (an operational record of actions taken, not itself farmer-owned data)",
            "Other parties' own data (buyers/dealers/professionals), referenced here only by opaque id",
        ],
    }


def request_account_deletion(db: Session, farmer_id: str) -> None:
    farmer_uuid = uuid.UUID(farmer_id)
    user = db.get(User, farmer_uuid)
    if user is None:
        raise AppError(error_codes.NOT_FOUND, "Account not found.", 404)
    if user.status == AccountStatus.INACTIVE:
        raise AppError(error_codes.VALIDATION_ERROR, "This account is already deactivated.", 409)

    AuditLogger(db).log(
        "ACCOUNT_DELETION_REQUESTED", actor_id=farmer_id, actor_role="farmer", entity="user", entity_id=farmer_id
    )

    user.status = AccountStatus.INACTIVE
    user.phone_number = f"deleted-{uuid.uuid4().hex[:10]}"  # phone_number is VARCHAR(20) - "deleted-" (8) + 10 hex chars = 18
    user.email = None
    if user.farmer_profile is not None:
        user.farmer_profile.full_name = "Deleted Farmer"

    refresh_token_repository.revoke_all_for_user(db, farmer_uuid)

    db.commit()
