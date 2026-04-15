from fastapi.testclient import TestClient


def _register_payload() -> dict[str, str]:
    return {
        "name": "拆书服务",
        "task_type": "book_split",
        "description": "将书籍拆分为章节段落",
        "endpoint_url": "http://localhost:9001",
    }


def _register_processor(client: TestClient, **overrides: str) -> dict[str, object]:
    payload = _register_payload()
    payload.update(overrides)
    response = client.post("/api/processors/register", json=payload)
    assert response.status_code == 201
    return response.json()


def test_register_processor(client: TestClient) -> None:
    response = client.post("/api/processors/register", json=_register_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["processor_id"] > 0
    assert data["api_token"].startswith("sp_")
    assert data["message"] == "注册成功"


def test_register_processor_is_idempotent(client: TestClient) -> None:
    first = _register_processor(client)
    second = _register_processor(
        client,
        description="新的描述",
        endpoint_url="http://localhost:9002",
    )

    assert second["processor_id"] == first["processor_id"]
    assert second["api_token"] == first["api_token"]


def test_heartbeat_success(client: TestClient) -> None:
    registration = _register_processor(client, task_type="instruction")

    response = client.post(
        "/api/processors/heartbeat",
        json={"processor_id": registration["processor_id"]},
        headers={"Authorization": f"Bearer {registration['api_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_heartbeat_rejects_wrong_token(client: TestClient) -> None:
    registration = _register_processor(client, task_type="heartbeat")

    response = client.post(
        "/api/processors/heartbeat",
        json={"processor_id": registration["processor_id"]},
        headers={"Authorization": "Bearer sp_wrong_token"},
    )

    assert response.status_code == 403


def test_list_processors_is_available_for_admin_and_aggregator(
    authenticated_client,
    client: TestClient,
) -> None:
    _register_processor(client, task_type="grammar_fix")
    admin_client = authenticated_client("admin")
    aggregator_client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    admin_response = admin_client.get("/api/processors")
    aggregator_response = aggregator_client.get("/api/processors")
    provider_response = provider_client.get("/api/processors")

    assert admin_response.status_code == 200
    assert len(admin_response.json()) == 1
    assert admin_response.json()[0]["task_type"] == "grammar_fix"
    assert aggregator_response.status_code == 200
    assert aggregator_response.json()[0]["task_type"] == "grammar_fix"
    assert provider_response.status_code == 403
