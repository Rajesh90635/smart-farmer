import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.crop_cycle import CultivationStatus, FailureReason, Season
from app.models.plot import SoilCategory


class CropMasterResponse(BaseModel):
    id: uuid.UUID
    name: str
    local_names: dict | None
    scientific_name: str | None
    category: str | None

    model_config = {"from_attributes": True}


class CropCycleCreateRequest(BaseModel):
    crop_id: uuid.UUID
    season: Season | None = None
    sowing_date: date
    expected_harvest_date: date | None = None
    seed_variety: str | None = Field(default=None, max_length=150)
    # Additive (Phase 1) - optional FK to a structured CropVariety.
    # Independent of seed_variety: a request can set neither, either, or
    # both. Omitting it entirely preserves pre-Phase-1 behavior exactly.
    variety_id: uuid.UUID | None = None
    # D10-10/D11-01: links a re-sown cycle back to the failed one it
    # replaces - optional, never required, so ordinary "plant a new crop"
    # creation is completely unaffected.
    resown_from_crop_cycle_id: uuid.UUID | None = None
    # D7-01 (docs/audit/FINAL_CANONICAL_group_A.md): a farmer who is still
    # preparing the land (not yet actually planned/sown) can start a cycle
    # there instead of at the default PLANNED. Deliberately restricted to
    # {LAND_PREPARATION, PLANNED} - this field creates the row, it must
    # never be used to skip past validation into a stage that implies work
    # (sowing, growth) which hasn't actually happened.
    initial_status: CultivationStatus = CultivationStatus.PLANNED

    @model_validator(mode="after")
    def validate_dates(self) -> "CropCycleCreateRequest":
        if self.expected_harvest_date is not None and self.expected_harvest_date < self.sowing_date:
            raise ValueError("expected_harvest_date cannot be before sowing_date")
        if self.initial_status not in (CultivationStatus.LAND_PREPARATION, CultivationStatus.PLANNED):
            raise ValueError("initial_status must be 'land_preparation' or 'planned'")
        return self


class CropFailureReportRequest(BaseModel):
    failure_reason: FailureReason
    # D10-07: required only when failure_reason is OTHER (validated in
    # crop_cycle_service.report_crop_failure, not here - Pydantic has no
    # clean way to make a field's requiredness depend on a sibling's
    # enum value without a bespoke validator, and the service layer
    # already owns every other cross-field rule in this file).
    failure_reason_note: str | None = Field(default=None, max_length=1000)


class CropCycleUpdateRequest(BaseModel):
    season: Season | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    seed_variety: str | None = Field(default=None, max_length=150)
    cultivation_status: CultivationStatus | None = None


class CropCycleClosureSnapshotResponse(BaseModel):
    """D97-02..09 (docs/audit/FINAL_CANONICAL_group_D.md): a frozen-at-close
    view - every field here is None only when the underlying real data
    genuinely didn't exist at closure time, never a fabricated placeholder."""
    harvest_quantity: Decimal | None
    harvest_quantity_unit: str | None
    quality_grade: str | None
    harvest_status: str | None
    actual_cost: Decimal | None
    actual_revenue: Decimal | None
    actual_profit_loss: Decimal | None
    disease_summary: dict | None
    weather_impact_summary: dict | None
    closed_at: datetime

    model_config = {"from_attributes": True}


class CropCycleCloseRequest(BaseModel):
    actual_harvest_date: date
    # D97-10 (docs/FINAL_GAP_REPORT.md): free-text farmer reflection,
    # optional, only ever settable at the moment of closing the cycle -
    # no other endpoint accepts or edits this field afterward.
    lessons_learned: str | None = Field(default=None, max_length=2000)


class CropCycleResponse(BaseModel):
    id: uuid.UUID
    plot_id: uuid.UUID
    crop: CropMasterResponse
    season: Season | None
    sowing_date: date
    expected_harvest_date: date | None
    actual_harvest_date: date | None
    cultivation_status: CultivationStatus
    seed_variety: str | None
    variety_id: uuid.UUID | None
    failure_reason: str | None = None
    failure_reason_note: str | None = None
    resown_from_crop_cycle_id: uuid.UUID | None = None
    # D19-05: pure join through to the plot's soil descriptors - read-only,
    # no new logic. See CropCycle.plot_soil_type/plot_soil_category.
    plot_soil_type: str | None = None
    plot_soil_category: SoilCategory | None = None
    # Only ever set by report_crop_failure() - never persisted, always None elsewhere.
    recommended_next_action: str | None = None
    # Only ever set by close_my_crop_cycle() - never editable afterward.
    lessons_learned: str | None = None
    # Only ever set by close_my_crop_cycle() - None before closure, frozen after.
    closure_snapshot: CropCycleClosureSnapshotResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropCycleListResponse(BaseModel):
    items: list[CropCycleResponse]
    total: int
