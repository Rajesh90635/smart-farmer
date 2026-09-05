"""
Tests for the Expert SLA sweep (app/services/case_sla_service.py) - the
concrete implementation of D34-03 (timeout reassignment), D35-02 (SLA
monitoring), D35-03 (reminder), D35-04 (breach escalation), D35-05
(expert unavailable) and D80-01 (CRITICAL notification priority actually
reachable), per docs/audit/c06_expert_network.md and
docs/audit/c12_notifications_offline_sync.md.

The scheduler itself (app/services/scheduler.py) is disabled in the
`testing` environment - these tests call `run_case_sla_sweep` directly,
exactly like the scheduler's own job function does, using the shared
`db_session` fixture so assertions can see uncommitted-by-the-test-but-
committed-by-the-sweep state without a second connection.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security_passwords import hash_password
from app.models.case_assignment import AssignmentStatus, CaseAssignment
from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
from app.models.user import User
from app.services.case_sla_service import run_case_sla_sweep
from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.professional_factories import unique_phone, valid_case_payload


def _create_verified_professional(db, *, display_name="Verified Expert"):
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProfessionalProfile(
        user_id=user.id,
        role="expert",
        display_name=display_name,
        verification_status=VerificationStatus.VERIFIED,
        availability_status=AvailabilityStatus.AVAILABLE,
        language_codes=["en"],
        crop_specialization_ids=[],
        disease_specialization_categories=[],
        service_area={"state": "Kerala", "district": "Thrissur"},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _create_crop_cycle(client, tokens, sample_crop_id):
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    return cycle["id"]


def _create_case(client, tokens, crop_cycle_id):
    return client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(tokens)).json()


def test_sweep_sends_one_reminder_before_expiry_and_never_duplicates(client, registered_farmer, sample_crop_id, db_session):
    _, farmer_tokens = registered_farmer
    _create_verified_professional(db_session)
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = _create_case(client, farmer_tokens, crop_cycle_id)
    assert case["status"] == "assigned"

    assignment = db_session.execute(
        select(CaseAssignment).where(CaseAssignment.case_id == uuid.UUID(case["id"]))
    ).scalar_one()
    assignment.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # inside the 4h reminder window
    db_session.commit()

    settings = get_settings()
    first = run_case_sla_sweep(db_session, settings)
    assert first.reminders_sent == 1

    second = run_case_sla_sweep(db_session, settings)
    assert second.reminders_sent == 0  # notification dedup_key blocks a repeat


def test_sweep_expires_stale_assignment_and_reassigns_excluding_the_non_responder(
    client, registered_farmer, sample_crop_id, db_session
):
    _, farmer_tokens = registered_farmer
    _create_verified_professional(db_session, display_name="Expert A")
    _create_verified_professional(db_session, display_name="Expert B")
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = _create_case(client, farmer_tokens, crop_cycle_id)
    case_id = uuid.UUID(case["id"])
    assert case["status"] == "assigned"

    assignment = db_session.execute(
        select(CaseAssignment).where(CaseAssignment.case_id == case_id)
    ).scalar_one()
    non_responder_id = assignment.professional_id
    assignment.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    settings = get_settings()
    result = run_case_sla_sweep(db_session, settings)
    assert result.expired == 1
    assert result.reassigned == 1

    assignments = db_session.execute(select(CaseAssignment).where(CaseAssignment.case_id == case_id)).scalars().all()
    assert len(assignments) == 2
    expired_row = next(a for a in assignments if a.id == assignment.id)
    new_row = next(a for a in assignments if a.id != assignment.id)
    assert expired_row.status == AssignmentStatus.EXPIRED
    assert new_row.status == AssignmentStatus.PENDING
    assert new_row.professional_id != non_responder_id  # never re-offered to the non-responder

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["status"] == "assigned"


def test_sweep_escalates_after_repeated_timeouts_with_critical_notification(
    client, registered_farmer, sample_crop_id, db_session
):
    _, farmer_tokens = registered_farmer
    _create_verified_professional(db_session, display_name="Initial Expert")
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = _create_case(client, farmer_tokens, crop_cycle_id)
    case_id = uuid.UUID(case["id"])
    assert case["status"] == "assigned"

    now = datetime.now(timezone.utc)
    # Simulate 2 professionals who already timed out on this case before
    # this sweep (case_sla_max_reassignment_attempts defaults to 2).
    for i in range(2):
        professional = _create_verified_professional(db_session, display_name=f"Timed-out Expert {i}")
        db_session.add(
            CaseAssignment(
                case_id=case_id, professional_id=professional.id,
                status=AssignmentStatus.EXPIRED, expires_at=now - timedelta(hours=1),
            )
        )
    db_session.commit()

    # The currently-live assignment (from case creation) is now overdue too - the 3rd timeout.
    live_assignment = db_session.execute(
        select(CaseAssignment).where(CaseAssignment.case_id == case_id, CaseAssignment.status == AssignmentStatus.PENDING)
    ).scalar_one()
    live_assignment.expires_at = now - timedelta(minutes=1)
    db_session.commit()

    settings = get_settings()
    result = run_case_sla_sweep(db_session, settings)
    assert result.expired == 1
    assert result.escalated == 1
    assert str(case_id) in result.case_ids_escalated

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["status"] == "escalated"

    notifications = client.get("/api/v1/notifications", headers=auth_headers(farmer_tokens)).json()["items"]
    critical = [n for n in notifications if n["priority"] == "critical"]
    assert len(critical) == 1


def test_sweep_notifies_farmer_on_every_distinct_reassignment_not_just_the_first(
    client, registered_farmer, sample_crop_id, db_session
):
    """Regression guard: a farmer-facing CASE_REASSIGNED notification's
    dedup key must include the NEW assignment's id, not just the case id
    - otherwise a case reassigned more than once would have its second
    notification silently swallowed by the same dedup_key as the first."""
    _, farmer_tokens = registered_farmer
    _create_verified_professional(db_session, display_name="Expert A")
    _create_verified_professional(db_session, display_name="Expert B")
    _create_verified_professional(db_session, display_name="Expert C")
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = _create_case(client, farmer_tokens, crop_cycle_id)
    case_id = uuid.UUID(case["id"])
    settings = get_settings()

    def _expire_current_pending():
        assignment = db_session.execute(
            select(CaseAssignment).where(CaseAssignment.case_id == case_id, CaseAssignment.status == AssignmentStatus.PENDING)
        ).scalar_one()
        assignment.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()

    _expire_current_pending()
    assert run_case_sla_sweep(db_session, settings).reassigned == 1

    _expire_current_pending()
    assert run_case_sla_sweep(db_session, settings).reassigned == 1

    notifications = client.get("/api/v1/notifications", headers=auth_headers(farmer_tokens)).json()["items"]
    reassigned_notifications = [
        n for n in notifications
        if n["related_entity_id"] == str(case_id)
        and n["body"] == "Your case has been assigned to another available professional."
    ]
    assert len(reassigned_notifications) == 2


def test_sweep_never_reopens_a_case_the_farmer_already_closed(client, registered_farmer, sample_crop_id, db_session):
    """A PENDING assignment can outlive a case the farmer independently
    closed/cancelled through another path - the sweep must not resurrect it."""
    _, farmer_tokens = registered_farmer
    _create_verified_professional(db_session)
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = _create_case(client, farmer_tokens, crop_cycle_id)
    case_id = uuid.UUID(case["id"])

    client.post(f"/api/v1/cases/{case['id']}/close", headers=auth_headers(farmer_tokens))

    assignment = db_session.execute(select(CaseAssignment).where(CaseAssignment.case_id == case_id)).scalar_one()
    assignment.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    settings = get_settings()
    result = run_case_sla_sweep(db_session, settings)
    assert result.expired == 0
    assert result.escalated == 0

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["status"] == "closed"
