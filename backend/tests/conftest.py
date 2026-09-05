import os

import pytest
from fastapi.testclient import TestClient

# Test environment variables must be set BEFORE importing app.main, since
# Settings() is constructed at import time via get_settings().
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:Admin123@localhost:5432/smart_farmer_test"
)
os.environ.setdefault("JWT_SIGNING_KEY", "test-only-signing-key-not-for-production-use")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402

from tests.factories import valid_register_payload  # noqa: E402,F401


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def registered_farmer(client, valid_register_payload):
    """Registers a fresh farmer and returns (payload, tokens) for tests
    that need an already-authenticated user rather than testing
    registration itself."""
    payload = valid_register_payload()
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload, response.json()


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def another_farmer(client, valid_register_payload):
    """A second, independent farmer - for ownership/cross-access tests."""
    payload = valid_register_payload()
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload, response.json()


@pytest.fixture()
def sample_crop_id(db_session):
    from sqlalchemy import select

    from app.models.crop_master import CropMaster

    crop = db_session.execute(select(CropMaster).where(CropMaster.name == "Tomato")).scalar_one()
    return str(crop.id)


@pytest.fixture()
def farmer_with_crop_cycle(client, registered_farmer, sample_crop_id):
    """Registers a farmer and creates a full Farm -> Plot -> CropCycle
    chain, returning (tokens, crop_cycle_id) - saves every photo test from
    repeating this four-call setup."""
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    _, tokens = registered_farmer
    headers = auth_headers(tokens)

    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    ).json()

    return tokens, cycle["id"]


@pytest.fixture()
def uploaded_photo(client, farmer_with_crop_cycle):
    """Creates a session and uploads one valid, quality-accepted photo -
    returns (tokens, crop_cycle_id, photo_id) for AI analysis tests."""
    import io

    from tests.photo_factories import make_test_jpeg, valid_photo_session_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    ).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": "ai-test-upload-1", "source": "camera"}
    photo = client.post(
        f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)
    ).json()
    return tokens, crop_cycle_id, photo["id"], session["id"]


def override_model_provider(fake_provider):
    """Overrides the app's model-provider dependency for the duration of a
    `with` block, then restores it - so tests never leak a fake provider
    into other tests."""
    from contextlib import contextmanager

    from app.core.ai_model_dependency import get_model_provider
    from app.main import app

    @contextmanager
    def _ctx():
        app.dependency_overrides[get_model_provider] = lambda: fake_provider
        try:
            yield
        finally:
            app.dependency_overrides.pop(get_model_provider, None)

    return _ctx()


def override_weather_provider(fake_provider):
    """Same pattern as override_model_provider, for weather."""
    from contextlib import contextmanager

    from app.core.weather_provider_dependency import get_weather_provider
    from app.main import app

    @contextmanager
    def _ctx():
        app.dependency_overrides[get_weather_provider] = lambda: fake_provider
        try:
            yield
        finally:
            app.dependency_overrides.pop(get_weather_provider, None)

    return _ctx()


def override_sms_provider(fake_provider):
    """Same pattern as override_model_provider, for SMS/OTP."""
    from contextlib import contextmanager

    from app.core.sms_provider_dependency import get_sms_provider
    from app.main import app

    @contextmanager
    def _ctx():
        app.dependency_overrides[get_sms_provider] = lambda: fake_provider
        try:
            yield
        finally:
            app.dependency_overrides.pop(get_sms_provider, None)

    return _ctx()


@pytest.fixture()
def farmer_with_located_farm(client, registered_farmer):
    """Registers a farmer and creates a farm WITH a latitude/longitude -
    needed for weather tests since weather requires a farm location."""
    from tests.farm_factories import valid_farm_payload

    _, tokens = registered_farmer
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    return tokens, farm["id"]


@pytest.fixture()
def verified_expert(client):
    """Registers a NEW farmer-role user, assigns them the expert role
    directly in the DB (since role-switching isn't a built endpoint),
    creates+verifies a ProfessionalProfile, returns (tokens, professional_id)."""
    import uuid as uuid_mod

    from app.core.jwt import create_access_token
    from app.db.session import SessionLocal
    from app.models.professional_profile import ProfessionalProfile, VerificationStatus, AvailabilityStatus
    from app.models.user import User
    from app.core.security_passwords import hash_password
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProfessionalProfile(
        user_id=user.id,
        role="expert",
        display_name="Verified Expert",
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

    access_token = create_access_token(subject=str(user.id), role="expert")
    tokens = {"access_token": access_token, "refresh_token": "n/a"}
    professional_id = str(profile.id)
    db.close()
    return tokens, professional_id


@pytest.fixture()
def verified_dealer(client):
    """Same pattern as verified_expert, for role='dealer'."""
    import uuid as uuid_mod

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
        user_id=user.id,
        role="dealer",
        display_name="Verified Dealer",
        verification_status=VerificationStatus.VERIFIED,
        availability_status=AvailabilityStatus.AVAILABLE,
        service_area={"state": "Kerala", "district": "Thrissur"},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    access_token = create_access_token(subject=str(user.id), role="dealer")
    tokens = {"access_token": access_token, "refresh_token": "n/a"}
    dealer_id = str(profile.id)
    db.close()
    return tokens, dealer_id


@pytest.fixture()
def admin_tokens(client):
    import uuid as uuid_mod

    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.user import User
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), role="admin")
    db.close()
    return {"access_token": token, "refresh_token": "n/a"}


@pytest.fixture()
def approved_product(client, admin_tokens):
    from tests.marketplace_factories import valid_product_payload

    product = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()
    approved = client.post(f"/api/v1/products/{product['id']}/approve", json={}, headers=auth_headers(admin_tokens)).json()
    return approved


@pytest.fixture()
def verified_buyer(client):
    """Same pattern as verified_dealer, for role='buyer' + BuyerBusinessProfile."""
    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.buyer_business_profile import BuyerBusinessProfile, BuyerType
    from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
    from app.models.user import User
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProfessionalProfile(
        user_id=user.id,
        role="buyer",
        display_name="Verified Buyer",
        verification_status=VerificationStatus.VERIFIED,
        availability_status=AvailabilityStatus.AVAILABLE,
        service_area={"state": "Kerala", "district": "Thrissur"},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    business_profile = BuyerBusinessProfile(professional_id=profile.id, buyer_type=BuyerType.WHOLESALER, min_quantity=100, max_quantity=5000)
    db.add(business_profile)
    db.commit()

    access_token = create_access_token(subject=str(user.id), role="buyer")
    tokens = {"access_token": access_token, "refresh_token": "n/a"}
    buyer_id = str(profile.id)
    db.close()
    return tokens, buyer_id
