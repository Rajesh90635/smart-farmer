"""
Phase 35: Crop Health Timeline.

This is a PURE READ/AGGREGATION service - it introduces no new table
and stores nothing. Every event is built directly from an existing,
already-tested repository's real rows.

EXCLUDED, with the reason documented here (not silently dropped):
- Weather/crop-action events: Notification has no crop_cycle_id
  anywhere in its schema (confirmed by inspection) - only farm_id. A
  farm can have multiple crop cycles, so there is no reliable way to
  attribute a weather alert to ONE specific crop cycle without
  fabricating a relationship that doesn't exist in the data model.
- Task completion events: Task is purely operational (irrigation,
  spraying, fertilizing, weeding, harvesting, general, other) - not a
  health/disease fact, and already covered by a different existing
  concept (Phase 33's Operational Task Risk factor).

ORDERING RULE (deterministic, documented): events are sorted by
event_datetime DESCENDING (most recent first, matching every other list
screen in this project). Date-only source fields (TreatmentRecord
.application_date, TreatmentFollowUp.observation_date, HarvestRecord
.actual_harvest_date) are converted to midnight UTC for comparison - a
disclosed limitation, since no time-of-day was ever captured for these
fields to begin with. Ties are broken first by a fixed event-type
priority order (_EVENT_TYPE_PRIORITY below), then by the underlying
record's own UUID as an absolute final tiebreaker.
"""
import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ai_analysis import ResultStatus
from app.repositories import (
    ai_analysis_repository,
    case_repository,
    crop_cycle_repository,
    crop_cycle_stage_history_repository,
    crop_photo_repository,
    harvest_repository,
    treatment_repository,
)
from app.schemas.health_timeline import CropHealthTimelineResponse, TimelineEvent
from app.services import treatment_service

_EVENT_TYPE_PRIORITY = {
    "crop_cycle_started": 0,
    "stage_changed": 1,
    "photo_captured": 2,
    "ai_analysis": 3,
    "health_case_created": 4,
    "case_reviewed": 5,
    "treatment_applied": 6,
    "treatment_follow_up": 7,
    "harvested": 8,
}

_HEALTH_STATUS_LABELS = {
    ResultStatus.HEALTHY.value: "Healthy",
    ResultStatus.DISEASE_DETECTED.value: "Disease detected",
    ResultStatus.LOW_CONFIDENCE.value: "Health check inconclusive",
    ResultStatus.CROP_MISMATCH.value: "Health check inconclusive",
    ResultStatus.UNKNOWN.value: "Health check inconclusive",
    ResultStatus.PROCESSING.value: "Analysis in progress",
    ResultStatus.FAILED.value: "Analysis failed",
    ResultStatus.AI_UNAVAILABLE.value: "Analysis unavailable",
}


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    raise TypeError(f"Unsupported timestamp type: {type(value)}")


def get_health_timeline(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropHealthTimelineResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    events: list[TimelineEvent] = []

    events.append(
        TimelineEvent(
            event_type="crop_cycle_started",
            event_datetime=_to_datetime(crop_cycle.created_at),
            title="Crop cycle started",
            description="This crop cycle was created.",
            source_id=crop_cycle.id,
        )
    )

    for stage in crop_cycle_stage_history_repository.list_for_crop_cycle(db, crop_cycle_id):
        events.append(
            TimelineEvent(
                event_type="stage_changed",
                event_datetime=_to_datetime(stage.entered_at),
                title="Crop stage changed",
                description=f"Crop cycle entered the '{stage.status.value}' stage.",
                source_id=stage.id,
            )
        )

    photos = crop_photo_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    analyzed_photo_ids = {a.crop_photo_id for a in analyses if a.crop_photo_id is not None}

    for photo in photos:
        if photo.id in analyzed_photo_ids:
            continue
        events.append(
            TimelineEvent(
                event_type="photo_captured",
                event_datetime=_to_datetime(photo.created_at),
                title="Crop photo captured",
                description="A crop photo was captured and has not yet been analyzed.",
                source_id=photo.id,
                photo_id=photo.id,
            )
        )

    for analysis in analyses:
        status_label = _HEALTH_STATUS_LABELS.get(analysis.result_status.value, "Health check inconclusive")
        events.append(
            TimelineEvent(
                event_type="ai_analysis",
                event_datetime=_to_datetime(analysis.created_at),
                title="Crop health analysis",
                description=f"AI crop photo analysis result: {status_label}.",
                source_id=analysis.id,
                health_status=analysis.result_status.value,
                photo_id=analysis.crop_photo_id,
                analysis_id=analysis.id,
            )
        )

    for case in case_repository.list_cases_for_crop_cycle(db, crop_cycle_id, farmer_uuid):
        events.append(
            TimelineEvent(
                event_type="health_case_created",
                event_datetime=_to_datetime(case.created_at),
                title="Expert review requested",
                description="A crop health case was opened for expert/field-agent review.",
                source_id=case.id,
                case_id=case.id,
            )
        )
        for review in case_repository.list_reviews_for_case(db, case.id):
            events.append(
                TimelineEvent(
                    event_type="case_reviewed",
                    event_datetime=_to_datetime(review.created_at),
                    title="Expert review completed",
                    description=f"Reviewer outcome: {review.outcome.replace('_', ' ')}.",
                    source_id=review.id,
                    case_id=case.id,
                )
            )

    for treatment in treatment_repository.list_treatments_for_crop_cycle(db, crop_cycle_id, farmer_uuid):
        events.append(
            TimelineEvent(
                event_type="treatment_applied",
                event_datetime=_to_datetime(treatment.application_date),
                title="Treatment applied",
                description=treatment.notes or "A treatment was applied to this crop.",
                source_id=treatment.id,
                treatment_id=treatment.id,
            )
        )

        follow_ups = treatment_repository.list_follow_ups_for_treatment(db, treatment.id, farmer_uuid)
        if follow_ups:
            effectiveness = treatment_service.get_effectiveness(db, farmer_id, treatment.id)
            for follow_up in follow_ups:
                events.append(
                    TimelineEvent(
                        event_type="treatment_follow_up",
                        event_datetime=_to_datetime(follow_up.observation_date),
                        title="Treatment follow-up recorded",
                        description=_describe_follow_up(effectiveness.result),
                        source_id=follow_up.id,
                        treatment_id=treatment.id,
                    )
                )

    for harvest in harvest_repository.list_harvests_by_crop_cycle(db, crop_cycle_id):
        if harvest.actual_harvest_date is None:
            continue
        events.append(
            TimelineEvent(
                event_type="harvested",
                event_datetime=_to_datetime(harvest.actual_harvest_date),
                title="Crop harvested",
                description="A harvest was recorded for this crop cycle.",
                source_id=harvest.id,
            )
        )

    events.sort(key=lambda e: (-e.event_datetime.timestamp(), _EVENT_TYPE_PRIORITY.get(e.event_type, 99), str(e.source_id)))

    return CropHealthTimelineResponse(crop_cycle_id=crop_cycle_id, events=events)


def _describe_follow_up(effectiveness_result: str) -> str:
    if effectiveness_result == "improved":
        return "Follow-up recorded - treatment showed improvement."
    if effectiveness_result == "worsened":
        return "Follow-up recorded - crop health appears worse."
    if effectiveness_result == "no_significant_change":
        return "Follow-up recorded - no clear change observed."
    return "Follow-up recorded - not enough health analysis data to determine effectiveness."
