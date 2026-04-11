from io import BytesIO
from pathlib import Path

from app.core.config import settings


def test_consumer_only_sees_delivered_results(authenticated_client) -> None:
    admin_client = authenticated_client("admin")
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    consumer_client = authenticated_client("consumer")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "教材问答集",
            "data_type": "text",
            "granularity": "章节/问答",
            "version": "v1",
            "fields_description": "章节、问题、答案",
            "scale_description": "4200 条",
            "sensitivity_level": "internal",
            "description": "教材问答",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "教材问答交付需求",
            "purpose": "交付给数据使用者",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    task_response = aggregator_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_response.json()["id"],
            "config": {
                "model": "Qwen-2.5-72B",
                "prompt_template": "标准问答模板",
                "batch_size": "32",
            },
        },
    )
    task_id = task_response.json()["id"]
    aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始"},
    )
    aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed", "note": "结束"},
    )

    artifact_disk_path = Path(settings.upload_root) / "delivery" / str(demand_id) / "delivery.jsonl"
    artifact_disk_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_disk_path.write_text('{"delivery": true}\n', encoding="utf-8")

    aggregator_client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": artifact_disk_path.name,
            "file_path": f"uploads/delivery/{demand_id}/delivery.jsonl",
            "sample_count": 600,
            "note": "交付文件",
        },
    )

    response = consumer_client.get("/api/deliveries")
    assert response.status_code == 200
    assert response.json()[0]["demand_id"] == demand_id

    download_response = consumer_client.get(f"/api/deliveries/{demand_id}/download")
    assert download_response.status_code == 200

    forbidden_download = provider_client.get(f"/api/deliveries/{demand_id}/download")
    assert forbidden_download.status_code == 403

    logs_response = admin_client.get("/api/admin/logs")
    assert logs_response.status_code == 200
    actions = {item["action"] for item in logs_response.json()}
    assert "delivery.downloaded" in actions


def test_provider_cannot_read_consumer_delivery_list(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    admin_client = authenticated_client("admin")

    assert provider_client.get("/api/deliveries").status_code == 403
    assert aggregator_client.get("/api/deliveries").status_code == 403
    assert admin_client.get("/api/deliveries").status_code == 403


def test_admin_can_list_operation_logs(authenticated_client) -> None:
    admin_client = authenticated_client("admin")
    provider_client = authenticated_client("provider")

    provider_client.post(
        "/api/catalogs",
        json={
            "name": "日志目录",
            "data_type": "text",
            "granularity": "条目",
            "version": "v1",
            "fields_description": "标题、内容",
            "scale_description": "10 条",
            "sensitivity_level": "internal",
            "description": "审计日志测试",
        },
    )

    response = admin_client.get("/api/admin/logs")
    assert response.status_code == 200
    assert response.json()[0]["action"] == "catalog.created"


def test_admin_can_review_registration_and_see_audit_log(client, db_session) -> None:
    from app.core.security import hash_password
    from app.db.models.user import User, UserRole, UserStatus

    admin = User(
        username="admin",
        display_name="管理员",
        password_hash=hash_password("Admin123!"),
        email="admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(admin)
    db_session.commit()

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "review_me",
            "display_name": "待审核用户",
            "password": "Passw0rd!",
            "email": "review_me@example.com",
            "requested_role": "provider",
            "application_note": "申请测试审核日志",
        },
    )
    assert register_response.status_code == 201
    application_id = register_response.json()["id"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    token = login_response.json()["access_token"]

    approve_response = client.post(
        f"/api/admin/registrations/{application_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "provider", "review_note": "通过"},
    )
    assert approve_response.status_code == 200

    logs_response = client.get(
        "/api/admin/logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logs_response.status_code == 200
    assert logs_response.json()[0]["action"] == "registration.approved"
