from tests.conftest import auth_headers


def _chat(client, tokens, message):
    return client.post("/api/v1/assistant/chat", json={"message": message}, headers=auth_headers(tokens))


def test_crop_status_answer_uses_real_data(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _chat(client, tokens, "What is happening to my crop?")
    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"]["intent"] == "crop_status"
    assert "get_crop_status" in body["assistant_message"]["tools_called"]
    assert body["assistant_message"]["sources"]


def test_crop_status_with_no_crop_says_no_data_not_a_guess(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "What is happening to my crop?")
    body = response.json()
    assert body["assistant_message"]["confidence"] is None
    assert "don't have" in body["assistant_message"]["content"].lower()


def test_yield_style_question_with_no_data_says_i_dont_know(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "When should I harvest?")
    body = response.json()
    content = body["assistant_message"]["content"].lower()
    assert "5 ton" not in content and "tons" not in content
    assert "don't have" in content


def test_price_question_with_no_data_never_invents_a_price(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "What is today's seed price?")
    body = response.json()
    content = body["assistant_message"]["content"]
    import re

    assert not re.search(r"₹\s?\d", content), f"Response appears to contain an invented price: {content}"


def test_order_status_question_calls_real_order_service(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "Where is my order?")
    body = response.json()
    assert "get_my_orders" in body["assistant_message"]["tools_called"]


def test_weather_question_calls_real_weather_service(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    response = _chat(client, tokens, "Will it rain today?")
    body = response.json()
    assert "get_weather_status" in body["assistant_message"]["tools_called"]


def test_pesticide_question_never_prescribes(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "What pesticide should I use?")
    body = response.json()
    content = body["assistant_message"]["content"].lower()
    assert "expert" in content
    assert body["assistant_message"]["intent"] == "prescription_blocked"
    forbidden = ["ml/l", "kg/acre", "apply 5", "apply 10"]
    assert not any(term in content for term in forbidden)


def test_dosage_phrasing_variant_also_blocked(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "How much fungicide should I apply?")
    body = response.json()
    assert body["assistant_message"]["intent"] == "prescription_blocked"


def test_farmer_a_cannot_see_farmer_bs_conversation(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer

    conv = _chat(client, tokens_a, "What is happening to my crop?").json()["conversation_id"]

    response = client.get(f"/api/v1/assistant/history/{conv}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_farmer_a_cannot_delete_farmer_bs_conversation(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer

    conv = _chat(client, tokens_a, "What is happening to my crop?").json()["conversation_id"]

    response = client.delete(f"/api/v1/assistant/history/{conv}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_conversation_history_persists_and_is_retrievable(client, registered_farmer):
    _, tokens = registered_farmer
    first = _chat(client, tokens, "help").json()
    conv_id = first["conversation_id"]
    _chat(client, tokens, "What is happening to my crop?")

    history = client.get(f"/api/v1/assistant/history/{conv_id}", headers=auth_headers(tokens))
    assert history.status_code == 200
    assert len(history.json()["messages"]) == 4


def test_feedback_submission(client, registered_farmer):
    _, tokens = registered_farmer
    chat = _chat(client, tokens, "help").json()
    message_id = chat["assistant_message"]["id"]

    response = client.post(f"/api/v1/assistant/feedback/{message_id}", json={"feedback_type": "helpful"}, headers=auth_headers(tokens))
    assert response.status_code == 204


def test_preferences_default_and_update(client, registered_farmer):
    _, tokens = registered_farmer
    defaults = client.get("/api/v1/assistant/preferences", headers=auth_headers(tokens))
    assert defaults.status_code == 200
    assert defaults.json()["voice_enabled"] is False

    updated = client.put("/api/v1/assistant/preferences", json={"response_mode": "detailed"}, headers=auth_headers(tokens))
    assert updated.json()["response_mode"] == "detailed"


def test_daily_summary_never_invents_missing_data(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/assistant/daily-summary", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert len(response.json()["lines"]) >= 1


def test_daily_summary_includes_overdue_task_count_reusing_the_real_task_repository(client, farmer_with_crop_cycle, db_session):
    """Step 16 addition: this must reflect an ACTUAL overdue task in the
    database, never a fabricated count."""
    from datetime import date, timedelta
    import uuid

    from app.core.jwt import decode_access_token
    from app.models.task import Task

    tokens, crop_cycle_id = farmer_with_crop_cycle
    farmer_id = decode_access_token(tokens["access_token"])["sub"]
    db_session.add(Task(farmer_id=uuid.UUID(farmer_id), crop_cycle_id=uuid.UUID(crop_cycle_id), title="Overdue", due_date=date.today() - timedelta(days=2)))
    db_session.commit()

    response = client.get("/api/v1/assistant/daily-summary", headers=auth_headers(tokens))
    assert response.status_code == 200
    lines = response.json()["lines"]
    assert any("1 overdue task" in line for line in lines), f"Expected an overdue-task line, got: {lines}"


def test_help_intent(client, registered_farmer):
    _, tokens = registered_farmer
    response = _chat(client, tokens, "help")
    assert response.json()["assistant_message"]["intent"] == "help"


def test_unauthenticated_chat_rejected(client):
    response = client.post("/api/v1/assistant/chat", json={"message": "help"})
    assert response.status_code == 401
