from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.professional_factories import valid_case_payload


def _create_second_verified_expert():
    """D36-07: a genuinely different professional for the second-opinion
    flow to auto-assign to - mirrors conftest.py's verified_expert fixture
    body exactly (that fixture can't be invoked a second time within one
    test), avoiding the same professional's own (case_id, professional_id)
    unique constraint a real second-opinion auto-reassignment would also
    need a second professional to avoid."""
    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
    from app.models.user import User
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProfessionalProfile(
        user_id=user.id, role="expert", display_name="Second Verified Expert",
        verification_status=VerificationStatus.VERIFIED, availability_status=AvailabilityStatus.AVAILABLE,
        language_codes=["en"], crop_specialization_ids=[], disease_specialization_categories=[],
        service_area={"state": "Kerala", "district": "Thrissur"},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    access_token = create_access_token(subject=str(user.id), role="expert")
    return {"access_token": access_token, "refresh_token": "n/a"}


def _create_verified_field_agent():
    """D37-01: 'field_visit_required' is a FIELD_AGENT_OUTCOMES value, not
    an EXPERT_OUTCOMES one (see app/models/case_review.py) - a case
    reviewed by an expert can never produce this outcome, so the
    task-suggestion tests need a real field_agent professional."""
    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
    from app.models.user import User
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProfessionalProfile(
        user_id=user.id, role="field_agent", display_name="Verified Field Agent",
        verification_status=VerificationStatus.VERIFIED, availability_status=AvailabilityStatus.AVAILABLE,
        language_codes=["en"], crop_specialization_ids=[], disease_specialization_categories=[],
        service_area={"state": "Kerala", "district": "Thrissur"},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    access_token = create_access_token(subject=str(user.id), role="field_agent")
    return {"access_token": access_token, "refresh_token": "n/a"}


def _create_crop_cycle(client, tokens, sample_crop_id):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)).json()
    return cycle["id"]


def test_create_case_auto_assigns_to_verified_expert(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    _, professional_id = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    response = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "assigned"


def test_create_case_with_no_available_field_agent_waits_for_assignment(client, registered_farmer, sample_crop_id):
    """Requests field_agent specifically, since no test in this suite ever
    verifies a field_agent - this reliably has zero verified candidates,
    unlike 'expert' which accumulates verified professionals across the
    shared test database as other tests run."""
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    response = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, requested_professional_role="field_agent"), headers=auth_headers(farmer_tokens)
    )
    assert response.status_code == 201
    assert response.json()["status"] == "waiting_for_assignment"  # queued, not silently discarded


def test_invalid_professional_role_requested_is_rejected(client, registered_farmer, sample_crop_id):
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    response = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, requested_professional_role="dealer"), headers=auth_headers(farmer_tokens)
    )
    assert response.status_code == 422


def test_case_round_trips_symptom_description(client, registered_farmer, sample_crop_id):
    """D27-02 (docs/audit/FINAL_CANONICAL_group_B.md): optional free-text
    symptom description, persisted and readable back by the farmer. (No
    professional-facing case-detail endpoint exists yet - see D34-04 -
    so "surfaced to the professional" is verified only up to the point
    the data model/API make it available, not through a UI that doesn't
    exist.)"""
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)

    response = client.post(
        "/api/v1/cases",
        json=valid_case_payload(crop_cycle_id, symptom_description="Yellow spots on lower leaves, spreading upward"),
        headers=auth_headers(farmer_tokens),
    )
    assert response.status_code == 201
    case_id = response.json()["id"]
    assert response.json()["symptom_description"] == "Yellow spots on lower leaves, spreading upward"

    detail = client.get(f"/api/v1/cases/{case_id}", headers=auth_headers(farmer_tokens)).json()
    assert detail["symptom_description"] == "Yellow spots on lower leaves, spreading upward"


def test_case_without_symptom_description_defaults_to_none(client, registered_farmer, sample_crop_id):
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    response = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens))
    assert response.json()["symptom_description"] is None


def test_professional_accepts_case(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["status"] == "in_review"


def test_professional_declines_and_case_stays_traceable(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, professional_id = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/cases/{case['id']}/decline", headers=auth_headers(expert_tokens))
    assert response.status_code == 200
    assert response.json()["status"] == "declined"

    # The case itself is never silently discarded - either it was
    # reassigned to another verified expert (if one exists in the shared
    # test pool) or it's waiting for one. Either way, THIS professional's
    # own assignment record permanently shows "declined" (verified above),
    # which is what "the case stays traceable" actually means here.
    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["status"] in ("waiting_for_assignment", "assigned")


def test_declined_professional_is_never_reoffered_the_same_case(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, professional_id = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/decline", headers=auth_headers(expert_tokens))

    # The only verified expert declined - re-accepting must fail since
    # they were never re-assigned (no PENDING assignment for them exists).
    accept_attempt = client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    assert accept_attempt.status_code == 409  # their (declined) assignment row exists but isn't PENDING


def test_expert_submits_confirmed_review(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))

    response = client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens))
    assert response.status_code == 200
    assert response.json()["outcome"] == "confirmed"

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["status"] == "verified"
    assert case_after["final_verification_source"] == "expert"


def test_expert_disagreement_recorded_without_touching_ai_result(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))

    response = client.post(
        f"/api/v1/cases/{case['id']}/review",
        json={"outcome": "different_diagnosis", "alternative_disease_name": "Late Blight"},
        headers=auth_headers(expert_tokens),
    )
    assert response.status_code == 200

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["final_verified_class"] == "Late Blight"
    assert case_after["final_verification_source"] == "expert"


def test_review_can_cite_evidence_the_professional_has_a_grant_for(
    client, registered_farmer, sample_crop_id, verified_expert, uploaded_photo
):
    """D36-03 (docs/audit/FINAL_CANONICAL_group_B.md): a professional can
    cite the specific photo/analysis their outcome is based on."""
    expert_tokens, _ = verified_expert
    farmer_tokens_2, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider()
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(farmer_tokens_2)).json()

    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, crop_photo_id=photo_id), headers=auth_headers(farmer_tokens_2)
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))

    response = client.post(
        f"/api/v1/cases/{case['id']}/review",
        json={"outcome": "confirmed", "evidence_photo_ids": [photo_id], "evidence_analysis_ids": [analysis["id"]]},
        headers=auth_headers(expert_tokens),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["evidence_photo_ids"] == [photo_id]
    assert body["evidence_analysis_ids"] == [analysis["id"]]


def test_review_rejects_evidence_photo_the_professional_has_no_grant_for(
    client, registered_farmer, sample_crop_id, verified_expert, uploaded_photo
):
    expert_tokens, _ = verified_expert
    farmer_tokens_2, crop_cycle_id, photo_id, _ = uploaded_photo
    # No crop_photo_id on the case -> no PhotoAccessGrant is ever created.
    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens_2)
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))

    response = client.post(
        f"/api/v1/cases/{case['id']}/review",
        json={"outcome": "confirmed", "evidence_photo_ids": [photo_id]},
        headers=auth_headers(expert_tokens),
    )
    assert response.status_code == 403


def test_invalid_outcome_for_expert_role_is_rejected(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))

    # "healthy_looking" is a FIELD_AGENT outcome, not a valid expert one.
    response = client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "healthy_looking"}, headers=auth_headers(expert_tokens))
    assert response.status_code == 422


def test_cannot_review_without_accepting_first(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens))
    assert response.status_code == 409


def test_close_case_revokes_photo_access(client, registered_farmer, sample_crop_id, verified_expert, uploaded_photo):
    _, farmer_tokens = registered_farmer
    expert_tokens, professional_id = verified_expert
    farmer_tokens_2, crop_cycle_id, photo_id, _ = uploaded_photo
    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, crop_photo_id=photo_id), headers=auth_headers(farmer_tokens_2)
    ).json()

    close_response = client.post(f"/api/v1/cases/{case['id']}/close", headers=auth_headers(farmer_tokens_2))
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"


def test_second_opinion_respects_configured_limit(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()

    first = client.post(f"/api/v1/cases/{case['id']}/second-opinion", json={}, headers=auth_headers(farmer_tokens))
    assert first.status_code == 200

    second = client.post(f"/api/v1/cases/{case['id']}/second-opinion", json={}, headers=auth_headers(farmer_tokens))
    assert second.status_code == 409  # limit of 1 reached


def test_case_audit_trail_records_lifecycle_events(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens))

    audit = client.get(f"/api/v1/cases/{case['id']}/audit", headers=auth_headers(farmer_tokens))
    assert audit.status_code == 200
    actions = [a["action"] for a in audit.json()]
    assert "CASE_CREATED" in actions
    assert "CASE_ASSIGNED" in actions
    assert "CASE_ASSIGNMENT_ACCEPTED" in actions
    assert "CASE_REVIEW_SUBMITTED" in actions


def test_farmer_a_cannot_access_farmer_bs_case(client, registered_farmer, another_farmer, sample_crop_id, verified_expert):
    _, farmer_a_tokens = registered_farmer
    _, farmer_b_tokens = another_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_a_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_a_tokens)).json()

    response = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_b_tokens))
    assert response.status_code == 404


def test_farmer_feedback_after_review(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens))

    response = client.post(f"/api/v1/cases/{case['id']}/feedback", json={"helpful": True, "rating": 5}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 204


# --- D36-04: farmer acknowledgement ---

def test_farmer_can_acknowledge_a_review_and_it_is_idempotent(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    review = client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens)).json()
    assert review["acknowledged_at"] is None

    first = client.post(f"/api/v1/cases/{case['id']}/reviews/{review['id']}/acknowledge", headers=auth_headers(farmer_tokens))
    assert first.status_code == 200
    first_timestamp = first.json()["acknowledged_at"]
    assert first_timestamp is not None

    second = client.post(f"/api/v1/cases/{case['id']}/reviews/{review['id']}/acknowledge", headers=auth_headers(farmer_tokens))
    assert second.json()["acknowledged_at"] == first_timestamp  # idempotent - never overwritten


def test_farmer_a_cannot_acknowledge_farmer_bs_review(client, registered_farmer, another_farmer, sample_crop_id, verified_expert):
    _, farmer_a_tokens = registered_farmer
    _, farmer_b_tokens = another_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_a_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_a_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    review = client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens)).json()

    response = client.post(f"/api/v1/cases/{case['id']}/reviews/{review['id']}/acknowledge", headers=auth_headers(farmer_b_tokens))
    assert response.status_code == 404


# --- D36-07: recommendation version (supersedes_review_id) ---

def test_second_review_can_supersede_the_first_for_the_same_case(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    first_review = client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens)).json()
    assert first_review["supersedes_review_id"] is None

    second_expert_tokens = _create_second_verified_expert()
    client.post(f"/api/v1/cases/{case['id']}/second-opinion", json={}, headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(second_expert_tokens))
    second_review = client.post(
        f"/api/v1/cases/{case['id']}/review",
        json={"outcome": "different_diagnosis", "alternative_disease_name": "Late Blight", "supersedes_review_id": first_review["id"]},
        headers=auth_headers(second_expert_tokens),
    ).json()
    assert second_review["supersedes_review_id"] == first_review["id"]


def test_supersedes_review_id_rejects_a_review_from_a_different_case(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert

    crop_cycle_id_1 = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case_1 = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id_1), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case_1['id']}/accept", headers=auth_headers(expert_tokens))
    review_1 = client.post(f"/api/v1/cases/{case_1['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens)).json()

    crop_cycle_id_2 = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case_2 = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id_2), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case_2['id']}/accept", headers=auth_headers(expert_tokens))

    response = client.post(
        f"/api/v1/cases/{case_2['id']}/review",
        json={"outcome": "confirmed", "supersedes_review_id": review_1["id"]},
        headers=auth_headers(expert_tokens),
    )
    assert response.status_code == 404


# --- D37-01/02/03: recommendation -> task suggestion ---

def test_case_suggests_a_task_when_review_outcome_is_field_visit_required(client, registered_farmer, sample_crop_id):
    _, farmer_tokens = registered_farmer
    field_agent_tokens = _create_verified_field_agent()
    # farmer_dispute -> CasePriority.HIGH, so suggested_priority should be TaskPriority.HIGH (D37-03 bonus).
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post(
        "/api/v1/cases",
        json=valid_case_payload(crop_cycle_id, reason="farmer_dispute", requested_professional_role="field_agent"),
        headers=auth_headers(farmer_tokens),
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(field_agent_tokens))
    review = client.post(
        f"/api/v1/cases/{case['id']}/review", json={"outcome": "field_visit_required"}, headers=auth_headers(field_agent_tokens)
    ).json()

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["latest_review_id"] == review["id"]
    assert case_after["suggests_task"] is True
    assert case_after["suggested_task_type"] == "general"
    assert case_after["suggested_due_date"] is not None
    assert case_after["suggested_priority"] == "high"  # derived from the case's own real CasePriority.HIGH, D37-03


def test_case_does_not_suggest_a_task_for_a_non_suggesting_outcome(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(expert_tokens))
    client.post(f"/api/v1/cases/{case['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens))

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["suggests_task"] is False
    assert case_after["suggested_task_type"] is None
    assert case_after["suggested_due_date"] is None
    assert case_after["suggested_priority"] is None


def test_case_with_no_review_yet_never_suggests_a_task(client, registered_farmer, sample_crop_id):
    _, farmer_tokens = registered_farmer
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(farmer_tokens)).json()

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(farmer_tokens)).json()
    assert case_after["suggests_task"] is False
    assert case_after["latest_review_id"] is None


# --- D37-01/05/06: farmer-confirmed task creation from a suggestion, completion, treatment follow-up ---

def test_farmer_can_create_a_task_from_a_suggested_recommendation(client, registered_farmer, sample_crop_id):
    _, farmer_tokens = registered_farmer
    field_agent_tokens = _create_verified_field_agent()
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post(
        "/api/v1/cases",
        json=valid_case_payload(crop_cycle_id, requested_professional_role="field_agent"),
        headers=auth_headers(farmer_tokens),
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(field_agent_tokens))
    review = client.post(
        f"/api/v1/cases/{case['id']}/review", json={"outcome": "field_visit_required"}, headers=auth_headers(field_agent_tokens)
    ).json()

    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Field visit for expert recommendation", "source_case_review_id": review["id"]},
        headers=auth_headers(farmer_tokens),
    )
    assert task.status_code == 201
    task_body = task.json()
    assert task_body["source_case_review_id"] == review["id"]

    # D37-05: completes through the existing generic endpoint, no special handling needed.
    completed = client.post(f"/api/v1/tasks/{task_body['id']}/complete", headers=auth_headers(farmer_tokens))
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_task_creation_rejects_a_source_review_from_a_different_crop_cycle(client, registered_farmer, sample_crop_id, verified_expert):
    _, farmer_tokens = registered_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id_1 = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case_1 = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id_1), headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/cases/{case_1['id']}/accept", headers=auth_headers(expert_tokens))
    review = client.post(f"/api/v1/cases/{case_1['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens)).json()

    crop_cycle_id_2 = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_2}/tasks",
        json={"title": "Mismatched cycle", "source_case_review_id": review["id"]},
        headers=auth_headers(farmer_tokens),
    )
    assert response.status_code == 404


def test_task_creation_rejects_another_farmers_review(client, registered_farmer, another_farmer, sample_crop_id, verified_expert):
    _, farmer_a_tokens = registered_farmer
    _, farmer_b_tokens = another_farmer
    expert_tokens, _ = verified_expert
    crop_cycle_id_a = _create_crop_cycle(client, farmer_a_tokens, sample_crop_id)
    case_a = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id_a), headers=auth_headers(farmer_a_tokens)).json()
    client.post(f"/api/v1/cases/{case_a['id']}/accept", headers=auth_headers(expert_tokens))
    review_a = client.post(f"/api/v1/cases/{case_a['id']}/review", json={"outcome": "confirmed"}, headers=auth_headers(expert_tokens)).json()

    crop_cycle_id_b = _create_crop_cycle(client, farmer_b_tokens, sample_crop_id)
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_b}/tasks",
        json={"title": "Not my review", "source_case_review_id": review_a["id"]},
        headers=auth_headers(farmer_b_tokens),
    )
    assert response.status_code == 404


def test_treatment_can_link_back_to_a_source_task(client, registered_farmer, sample_crop_id):
    """D37-06 (docs/audit/FINAL_CANONICAL_group_B.md): reuses the existing
    effectiveness-comparison logic unchanged - this is a pure informational link."""
    _, farmer_tokens = registered_farmer
    field_agent_tokens = _create_verified_field_agent()
    crop_cycle_id = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    case = client.post(
        "/api/v1/cases",
        json=valid_case_payload(crop_cycle_id, requested_professional_role="field_agent"),
        headers=auth_headers(farmer_tokens),
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/accept", headers=auth_headers(field_agent_tokens))
    review = client.post(
        f"/api/v1/cases/{case['id']}/review", json={"outcome": "field_visit_required"}, headers=auth_headers(field_agent_tokens)
    ).json()
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Field visit", "source_case_review_id": review["id"]},
        headers=auth_headers(farmer_tokens),
    ).json()

    treatment = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-01-01", "source_task_id": task["id"]},
        headers=auth_headers(farmer_tokens),
    )
    assert treatment.status_code == 201
    assert treatment.json()["source_task_id"] == task["id"]


def test_treatment_rejects_a_source_task_from_a_different_crop_cycle(client, registered_farmer, sample_crop_id):
    _, farmer_tokens = registered_farmer
    crop_cycle_id_1 = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_1}/tasks", json={"title": "Some task"}, headers=auth_headers(farmer_tokens)
    ).json()

    crop_cycle_id_2 = _create_crop_cycle(client, farmer_tokens, sample_crop_id)
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_2}/treatments",
        json={"application_date": "2026-01-01", "source_task_id": task["id"]},
        headers=auth_headers(farmer_tokens),
    )
    assert response.status_code == 404
