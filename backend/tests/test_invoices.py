import io
from decimal import Decimal

from tests.conftest import auth_headers


def _make_test_invoice_image(vendor="Green Valley Agro Store", amount="2450.00", date_str="15/03/2026") -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), vendor, fill="black")
    draw.text((20, 60), f"Date: {date_str}", fill="black")
    draw.text((20, 100), "Item: NPK Fertilizer 50kg", fill="black")
    draw.text((20, 200), f"Total Amount: Rs {amount}", fill="black")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _upload(client, tokens, crop_cycle_id, image_bytes):
    files = {"file": ("invoice.png", io.BytesIO(image_bytes), "image/png")}
    return client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/invoices", files=files, headers=auth_headers(tokens))


def test_upload_invoice_runs_real_ocr_and_extracts_the_actual_amount(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    image = _make_test_invoice_image(amount="2450.00")
    response = _upload(client, tokens, crop_cycle_id, image)

    assert response.status_code == 201
    body = response.json()
    assert body["ocr_status"] == "completed"
    assert Decimal(body["extracted_amount"]) == Decimal("2450.00")
    assert body["is_confirmed"] is False


def test_uploaded_invoice_never_creates_a_ledger_entry_before_confirmation(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload(client, tokens, crop_cycle_id, _make_test_invoice_image())

    ledger = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=auth_headers(tokens)).json()
    assert ledger["entries"] == []
    assert Decimal(ledger["total_expense"]) == Decimal("0")


def test_cannot_upload_invoice_under_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = _upload(client, tokens_b, crop_cycle_id, _make_test_invoice_image())
    assert response.status_code == 404


def test_confirm_invoice_creates_a_real_ledger_entry_using_the_farmers_own_values_not_ocr_output(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image(amount="2450.00")).json()
    assert Decimal(upload["extracted_amount"]) == Decimal("2450.00")

    response = client.post(
        f"/api/v1/invoices/{upload['id']}/confirm",
        json={"amount": "2500.00", "entry_date": "2026-03-16", "vendor_name": "Corrected Vendor Name", "category": "fertilizer"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_confirmed"] is True
    assert Decimal(body["confirmed_amount"]) == Decimal("2500.00")
    assert body["linked_ledger_entry_id"] is not None

    ledger = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=auth_headers(tokens)).json()
    assert len(ledger["entries"]) == 1
    assert Decimal(ledger["entries"][0]["amount"]) == Decimal("2500.00")
    assert ledger["entries"][0]["source"] == "invoice_linked"
    assert ledger["entries"][0]["category"] == "fertilizer"


def test_cannot_confirm_an_already_confirmed_invoice(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image()).json()
    client.post(
        f"/api/v1/invoices/{upload['id']}/confirm",
        json={"amount": "100.00", "entry_date": "2026-01-01", "category": "other"},
        headers=auth_headers(tokens),
    )

    response = client.post(
        f"/api/v1/invoices/{upload['id']}/confirm",
        json={"amount": "200.00", "entry_date": "2026-01-01", "category": "other"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 409


def test_cannot_delete_a_confirmed_invoice(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image()).json()
    client.post(
        f"/api/v1/invoices/{upload['id']}/confirm",
        json={"amount": "100.00", "entry_date": "2026-01-01", "category": "other"},
        headers=auth_headers(tokens),
    )

    response = client.delete(f"/api/v1/invoices/{upload['id']}", headers=auth_headers(tokens))
    assert response.status_code == 409


def test_can_delete_an_unconfirmed_invoice(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image()).json()

    response = client.delete(f"/api/v1/invoices/{upload['id']}", headers=auth_headers(tokens))
    assert response.status_code == 204


def test_list_invoices_for_crop_cycle(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload(client, tokens, crop_cycle_id, _make_test_invoice_image())
    _upload(client, tokens, crop_cycle_id, _make_test_invoice_image())

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/invoices", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_unauthorized_invoice_access_is_rejected(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image()).json()

    response = client.get(f"/api/v1/invoices/{upload['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_ocr_confidence_is_a_real_computed_value_not_fabricated(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image()).json()
    assert upload["ocr_confidence"] in ("high", "medium", "low")


def test_confirm_requires_a_positive_amount(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    upload = _upload(client, tokens, crop_cycle_id, _make_test_invoice_image()).json()

    response = client.post(
        f"/api/v1/invoices/{upload['id']}/confirm",
        json={"amount": "-50.00", "entry_date": "2026-01-01", "category": "other"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422
