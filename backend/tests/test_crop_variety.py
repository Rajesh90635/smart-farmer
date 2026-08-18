import uuid

from sqlalchemy import select

from app.models.crop_master import CropMaster
from app.models.crop_variety import CropVariety
from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload


def _rice_crop_id(db_session) -> str:
    crop = db_session.execute(select(CropMaster).where(CropMaster.name == "Rice")).scalar_one()
    return str(crop.id)


def _unique(name: str) -> str:
    return f"{name} {uuid.uuid4().hex[:8]}"


def _create_variety(db_session, crop_id: str, name: str, typical_duration_days: int | None = None) -> str:
    variety = CropVariety(crop_id=uuid.UUID(crop_id), name=name, typical_duration_days=typical_duration_days)
    db_session.add(variety)
    db_session.commit()
    db_session.refresh(variety)
    return str(variety.id)


def test_empty_variety_list_for_a_crop_with_no_varieties(client, registered_farmer, db_session):
    """Uses a freshly created CropMaster row, not the shared seeded
    Tomato/Rice - those accumulate test-created varieties across runs
    against the same persistent test database, so relying on them for a
    guaranteed-empty assertion would be flaky."""
    fresh_crop = CropMaster(name=_unique("Test-Only Crop"), is_active=True)
    db_session.add(fresh_crop)
    db_session.commit()
    db_session.refresh(fresh_crop)

    _, tokens = registered_farmer
    response = client.get(f"/api/v1/crops/{fresh_crop.id}/varieties", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json() == []


def test_populated_variety_list_for_a_crop(client, registered_farmer, db_session):
    fresh_crop = CropMaster(name=_unique("Test-Only Crop"), is_active=True)
    db_session.add(fresh_crop)
    db_session.commit()
    db_session.refresh(fresh_crop)
    crop_id = str(fresh_crop.id)

    name_a, name_b = "Pusa Ruby", "Arka Rakshak"
    _create_variety(db_session, crop_id, name_a, typical_duration_days=120)
    _create_variety(db_session, crop_id, name_b)

    _, tokens = registered_farmer
    response = client.get(f"/api/v1/crops/{crop_id}/varieties", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    names = {v["name"] for v in body}
    assert names == {name_a, name_b}
    variety_a = next(v for v in body if v["name"] == name_a)
    assert variety_a["typical_duration_days"] == 120


def test_variety_list_only_returns_varieties_belonging_to_the_requested_crop(client, registered_farmer, sample_crop_id, db_session):
    rice_id = _rice_crop_id(db_session)
    tomato_name, rice_name = _unique("Pusa Ruby"), _unique("IR64")
    _create_variety(db_session, sample_crop_id, tomato_name)
    _create_variety(db_session, rice_id, rice_name)

    _, tokens = registered_farmer
    tomato_varieties = client.get(f"/api/v1/crops/{sample_crop_id}/varieties", headers=auth_headers(tokens)).json()
    rice_varieties = client.get(f"/api/v1/crops/{rice_id}/varieties", headers=auth_headers(tokens)).json()

    tomato_names = {v["name"] for v in tomato_varieties}
    rice_names = {v["name"] for v in rice_varieties}
    assert tomato_name in tomato_names and rice_name not in tomato_names
    assert rice_name in rice_names and tomato_name not in rice_names


def test_variety_list_for_nonexistent_crop_returns_404(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get(f"/api/v1/crops/{uuid.uuid4()}/varieties", headers=auth_headers(tokens))
    assert response.status_code == 404


def test_crop_cycle_creation_without_variety_id_still_works(client, registered_farmer, sample_crop_id):
    """Backward compatibility: omitting variety_id entirely must behave
    exactly as it did before Phase 1."""
    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()

    response = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["variety_id"] is None
    assert body["seed_variety"] == "Hybrid-1"


def test_crop_cycle_creation_with_valid_variety_id(client, registered_farmer, sample_crop_id, db_session):
    variety_id = _create_variety(db_session, sample_crop_id, _unique("Pusa Ruby"))

    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, variety_id=variety_id),
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["variety_id"] == variety_id
    # seed_variety (free text) is independent and still whatever was sent.
    assert body["seed_variety"] == "Hybrid-1"


def test_crop_cycle_cannot_reference_a_variety_belonging_to_another_crop(client, registered_farmer, sample_crop_id, db_session):
    rice_id = _rice_crop_id(db_session)
    rice_variety_id = _create_variety(db_session, rice_id, _unique("IR64"))

    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()

    # sample_crop_id is Tomato - deliberately sending a Rice variety_id.
    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, variety_id=rice_variety_id),
        headers=headers,
    )
    assert response.status_code == 422


def test_seed_variety_field_still_behaves_exactly_as_before(client, registered_farmer, sample_crop_id):
    """Guards against Phase 1 accidentally touching seed_variety's
    existing free-text behavior."""
    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, seed_variety="Some Free Text Variety"),
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["seed_variety"] == "Some Free Text Variety"
    assert response.json()["variety_id"] is None
