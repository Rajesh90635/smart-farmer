from tests.conftest import auth_headers
from tests.professional_factories import valid_case_payload


def test_assigned_expert_can_access_the_authorized_photo(client, uploaded_photo, verified_expert):
    farmer_tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    expert_tokens, _ = verified_expert

    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, crop_photo_id=photo_id), headers=auth_headers(farmer_tokens)
    ).json()
    assert case["status"] == "assigned"

    response = client.get(f"/api/v1/crop-photos/{photo_id}/file", headers=auth_headers(expert_tokens))
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_expert_without_a_grant_cannot_access_the_photo(client, uploaded_photo, verified_expert):
    """A DIFFERENT expert (no case, no grant) must not be able to access
    the photo just because they hold a valid EXPERT-role token."""
    farmer_tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    expert_tokens, _ = verified_expert  # never assigned to any case involving this photo

    response = client.get(f"/api/v1/crop-photos/{photo_id}/file", headers=auth_headers(expert_tokens))
    assert response.status_code == 404


def test_photo_access_is_revoked_after_case_closes(client, uploaded_photo, verified_expert):
    farmer_tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    expert_tokens, _ = verified_expert

    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, crop_photo_id=photo_id), headers=auth_headers(farmer_tokens)
    ).json()

    before_close = client.get(f"/api/v1/crop-photos/{photo_id}/file", headers=auth_headers(expert_tokens))
    assert before_close.status_code == 200

    client.post(f"/api/v1/cases/{case['id']}/close", headers=auth_headers(farmer_tokens))

    after_close = client.get(f"/api/v1/crop-photos/{photo_id}/file", headers=auth_headers(expert_tokens))
    assert after_close.status_code == 404


def test_photo_access_is_audited(client, uploaded_photo, verified_expert, db_session):
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    farmer_tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    expert_tokens, _ = verified_expert

    case = client.post(
        "/api/v1/cases", json=valid_case_payload(crop_cycle_id, crop_photo_id=photo_id), headers=auth_headers(farmer_tokens)
    ).json()
    client.get(f"/api/v1/crop-photos/{photo_id}/file", headers=auth_headers(expert_tokens))

    rows = db_session.execute(
        select(AuditLog).where(AuditLog.action == "CASE_PHOTO_ACCESSED", AuditLog.entity_id == case["id"])
    ).scalars().all()
    assert len(rows) >= 1
    assert rows[0].actor_role == "expert"


def test_farmer_still_retains_own_photo_access_regardless_of_case(client, uploaded_photo):
    farmer_tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    response = client.get(f"/api/v1/crop-photos/{photo_id}/file", headers=auth_headers(farmer_tokens))
    assert response.status_code == 200
