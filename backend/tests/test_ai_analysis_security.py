from tests.conftest import auth_headers


def test_unauthenticated_analyze_request_is_rejected(client, uploaded_photo):
    _, _, photo_id, _ = uploaded_photo
    response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze")
    assert response.status_code == 401


def test_farmer_a_cannot_analyze_farmer_bs_photo(client, uploaded_photo, another_farmer):
    _, _, photo_id, _ = uploaded_photo
    _, tokens_b = another_farmer

    response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_farmer_a_cannot_retrieve_farmer_bs_analysis(client, uploaded_photo, another_farmer):
    tokens_a, _, photo_id, _ = uploaded_photo
    _, tokens_b = another_farmer

    analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens_a)).json()

    get_by_id = client.get(f"/api/v1/ai/analysis/{analysis['id']}", headers=auth_headers(tokens_b))
    assert get_by_id.status_code == 404

    get_by_photo = client.get(f"/api/v1/crop-photos/{photo_id}/analysis", headers=auth_headers(tokens_b))
    assert get_by_photo.status_code == 404


def test_farmer_a_cannot_see_farmer_bs_analysis_history(client, uploaded_photo, another_farmer):
    tokens_a, crop_cycle_id, photo_id, _ = uploaded_photo
    _, tokens_b = another_farmer
    client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens_a))

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/analyses", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_ai_analysis_session_groups_multiple_photos(client, farmer_with_crop_cycle):
    import io

    from tests.photo_factories import make_test_jpeg, valid_photo_session_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    photo_session = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    ).json()

    for i in range(3):
        files = {"file": (f"leaf{i}.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
        data = {"client_upload_id": f"session-photo-{i}", "source": "camera"}
        client.post(
            f"/api/v1/crop-photo-sessions/{photo_session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)
        )

    ai_session = client.post(
        "/api/v1/ai/sessions", json={"crop_photo_session_id": photo_session["id"]}, headers=auth_headers(tokens)
    ).json()

    analyzed = client.post(f"/api/v1/ai/sessions/{ai_session['id']}/analyze", headers=auth_headers(tokens))
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert len(body["analyses"]) == 3
    # No combined/fused diagnosis is invented - each photo has its own
    # independent result_status.
    for analysis in body["analyses"]:
        assert analysis["result_status"] == "ai_unavailable"  # real default provider, honest


def test_cannot_create_ai_session_for_another_farmers_photo_session(client, farmer_with_crop_cycle, another_farmer):
    from tests.photo_factories import valid_photo_session_payload

    tokens_a, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer

    photo_session = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens_a)
    ).json()

    response = client.post(
        "/api/v1/ai/sessions", json={"crop_photo_session_id": photo_session["id"]}, headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404
