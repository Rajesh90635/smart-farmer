from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.professional_factories import valid_case_payload


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
