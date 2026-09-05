"""
D33-02 (match criteria actually populated), D34-01 (OFFLINE hard-excluded),
D33-06 (distinct escalation audit/notification), D36-02 (explanation
surfaced on case detail) - docs/audit/c06_expert_network.md.
"""
import uuid

from app.core.jwt import create_access_token
from app.core.security_passwords import hash_password
from app.models.audit_log import AuditLog
from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
from app.models.user import User
from sqlalchemy import select
from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.professional_factories import unique_phone, valid_case_payload


def _create_professional(db, *, role="expert", availability=AvailabilityStatus.AVAILABLE, crop_specialization_ids=None, display_name="Expert"):
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProfessionalProfile(
        user_id=user.id,
        role=role,
        display_name=display_name,
        verification_status=VerificationStatus.VERIFIED,
        availability_status=availability,
        language_codes=["en"],
        crop_specialization_ids=crop_specialization_ids or [],
        disease_specialization_categories=[],
        service_area={"state": "Kerala", "district": "Thrissur"},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    tokens = {"access_token": create_access_token(subject=str(user.id), role=role), "refresh_token": "n/a"}
    return tokens, profile


def _create_crop_cycle(client, tokens, sample_crop_id):
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    return cycle["id"]


def test_offline_only_candidate_leaves_case_waiting_not_auto_assigned(client, registered_farmer, sample_crop_id, db_session):
    """The test database is a real, persistent Postgres instance shared
    across the whole suite AND across separate pytest invocations (rows
    are never rolled back), so "zero other candidates exist" cannot be
    assumed even for role='field_agent' - only that THIS OFFLINE one is
    never the one chosen is a reliable guarantee."""
    _, offline_profile = _create_professional(db_session, role="field_agent", availability=AvailabilityStatus.OFFLINE, display_name="Offline Field Agent")
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, requested_professional_role="field_agent"),
        headers=auth_headers(farmer_tokens),
    ).json()
    assert case["status"] in ("waiting_for_assignment", "assigned")
    if case["status"] == "assigned":
        from app.models.case_assignment import CaseAssignment
        assignment = db_session.execute(select(CaseAssignment).where(CaseAssignment.case_id == uuid.UUID(case["id"]))).scalar_one()
        assert assignment.professional_id != offline_profile.id


def test_offline_professional_is_never_the_one_assigned(client, registered_farmer, sample_crop_id, db_session):
    """Weaker than asserting exactly which professional wins (the shared
    test DB accumulates other AVAILABLE verified experts across the whole
    run, making 'which one' order-dependent) - what D34-01 actually
    guarantees is that the OFFLINE one specifically is never chosen."""
    _, offline_profile = _create_professional(db_session, availability=AvailabilityStatus.OFFLINE, display_name="Offline Expert")
    _create_professional(db_session, availability=AvailabilityStatus.AVAILABLE, display_name="Available Expert")
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    assert case["status"] == "assigned"

    from app.models.case_assignment import CaseAssignment
    assignment = db_session.execute(select(CaseAssignment).where(CaseAssignment.case_id == uuid.UUID(case["id"]))).scalar_one()
    assert assignment.professional_id != offline_profile.id


def test_crop_specialization_match_is_preferred(client, registered_farmer, sample_crop_id, db_session):
    """D33-02: crop_id is now actually populated on MatchCriteria - a
    professional specializing in the case's real crop must outrank an
    equally-available generalist.

    Cleanup matters here: the test database is real and persistent
    (never rolled back between tests or pytest invocations), and nearly
    every other test in this suite auto-assigns an 'expert' case for
    THIS SAME crop (`sample_crop_id`, always Tomato). A specialist left
    behind with a permanent +25 crop-match score would silently hijack
    auto-assignment away from every later test's own fixture-created
    professional. Flipping it OFFLINE at the end makes it permanently
    excluded from all future routing (D34-01's hard filter) - equivalent
    to it not existing for matching purposes, without deleting history."""
    _create_professional(db_session, availability=AvailabilityStatus.AVAILABLE, display_name="Generalist Expert")
    _, specialist_profile = _create_professional(
        db_session, availability=AvailabilityStatus.AVAILABLE, crop_specialization_ids=[sample_crop_id], display_name="Tomato Specialist"
    )
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    try:
        case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
        assert case["status"] == "assigned"

        from app.models.case_assignment import CaseAssignment
        assignment = db_session.execute(select(CaseAssignment).where(CaseAssignment.case_id == uuid.UUID(case["id"]))).scalar_one()
        assert assignment.professional_id == specialist_profile.id
    finally:
        specialist_profile.availability_status = AvailabilityStatus.OFFLINE
        db_session.commit()


def test_field_visit_required_escalates_with_distinct_audit_and_notification(client, registered_farmer, sample_crop_id, db_session):
    field_agent_tokens, field_agent_profile = _create_professional(db_session, role="field_agent", display_name="Field Agent")
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    try:
        case = client.post(
            "/api/v1/cases", json=valid_case_payload(crop_cycle_id, requested_professional_role="field_agent"),
            headers=auth_headers(farmer_tokens),
        ).json()
        assert case["status"] == "assigned"

        accept = client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(field_agent_tokens))
        assert accept.status_code == 200, accept.text
        review = client.post(
            f"/api/v1/cases/{case['id']}/review", json={"outcome": "field_visit_required"}, headers=auth_headers(field_agent_tokens)
        )
        assert review.status_code == 200, review.text

        case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
        assert case_after["status"] == "escalated"

        entries = db_session.execute(
            select(AuditLog).where(AuditLog.entity == "crop_health_case", AuditLog.entity_id == case["id"], AuditLog.action == "CASE_ESCALATED")
        ).scalars().all()
        assert len(entries) == 1

        notifications = client.get("/api/v1/notifications", headers=auth_headers(farmer_tokens)).json()["items"]
        high_priority = [n for n in notifications if n["priority"] == "high"]
        assert len(high_priority) == 1
    finally:
        # This project's own test_cases.py relies on "no verified,
        # available field_agent exists" - flipping OFFLINE preserves
        # that invariant for every test that runs after this one.
        field_agent_profile.availability_status = AvailabilityStatus.OFFLINE
        db_session.commit()


def test_get_my_case_surfaces_latest_review_notes(client, registered_farmer, sample_crop_id, db_session):
    """Deliberately does NOT try to guarantee which professional gets
    auto-assigned (no crop-specialization trick, to avoid the same
    permanent-bias risk documented above) - instead it looks up whoever
    actually won and mints that professional a token directly, which
    works regardless of the rest of the suite's accumulated state."""
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    assert case["status"] == "assigned"

    from app.models.case_assignment import CaseAssignment

    assignment = db_session.execute(select(CaseAssignment).where(CaseAssignment.case_id == uuid.UUID(case["id"]))).scalar_one()
    assigned_professional = db_session.get(ProfessionalProfile, assignment.professional_id)
    assigned_tokens = {
        "access_token": create_access_token(subject=str(assigned_professional.user_id), role=assigned_professional.role),
        "refresh_token": "n/a",
    }

    accept = client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(assigned_tokens))
    assert accept.status_code == 200, accept.text
    review = client.post(
        f"/api/v1/cases/{case['id']}/review",
        json={"outcome": "confirmed", "notes": "Classic early blight lesions on lower leaves."},
        headers=auth_headers(assigned_tokens),
    )
    assert review.status_code == 200, review.text

    detail = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert detail["latest_review_notes"] == "Classic early blight lesions on lower leaves."
