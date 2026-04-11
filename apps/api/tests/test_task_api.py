from io import BytesIO
from pathlib import Path

from app.core.config import settings


def test_aggregator_can_create_task_after_data_upload(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    client = authenticated_client("aggregator")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "科研摘要",
            "data_type": "text",
            "granularity": "项目/摘要",
            "version": "v1",
            "fields_description": "项目名、摘要",
            "scale_description": "3200 条",
            "sensitivity_level": "internal",
            "description": "科研摘要数据",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    demand_response = client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "摘要转指令需求",
            "purpose": "一期指令生成半接入",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    upload_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    asset_id = upload_response.json()["id"]

    response = client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_id,
            "config": {
                "model": "Qwen-2.5-72B",
                "prompt_template": "标准问答模板",
                "batch_size": "32",
            },
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "queued"


def test_task_can_transition_to_completed_with_artifact(authenticated_client) -> None:
    client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "教育问答集",
            "data_type": "text",
            "granularity": "主题/帖子/回复",
            "version": "v1",
            "fields_description": "标题、正文、回复",
            "scale_description": "12000 条",
            "sensitivity_level": "internal",
            "description": "教育问答",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "教育问答指令需求",
            "purpose": "做半接入指令任务",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    task_response = client.post(
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

    running_response = client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始处理"},
    )
    assert running_response.status_code == 200

    completed_response = client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed", "note": "已完成"},
    )
    assert completed_response.status_code == 200

    artifact_disk_path = (
        Path(settings.upload_root) / "processed" / str(task_id) / "instruction-batch-1.jsonl"
    )
    artifact_disk_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_disk_path.write_text('{"ok": true}\n', encoding="utf-8")

    artifact_response = client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": artifact_disk_path.name,
            "file_path": f"uploads/processed/{task_id}/instruction-batch-1.jsonl",
            "sample_count": 1200,
            "note": "一期半接入产物登记",
        },
    )
    assert artifact_response.status_code == 201


def test_failed_task_requires_explicit_reason(authenticated_client) -> None:
    aggregator_client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "失败任务测试集",
            "data_type": "text",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "300 条",
            "sensitivity_level": "internal",
            "description": "失败原因校验",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "失败任务需求",
            "purpose": "验证失败原因必填",
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
            "config": {"model": "Qwen-2.5-72B"},
        },
    )
    task_id = task_response.json()["id"]
    aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始处理"},
    )

    invalid_response = aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "failed", "note": ""},
    )
    assert invalid_response.status_code == 422

    failed_response = aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "failed", "note": "模型调用失败"},
    )
    assert failed_response.status_code == 200
    assert failed_response.json()["status"] == "failed"
    assert failed_response.json()["note"] == "模型调用失败"


def test_aggregator_cannot_create_task_for_other_requester_demand(authenticated_client) -> None:
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "归属校验数据集",
            "data_type": "text",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "300 条",
            "sensitivity_level": "internal",
            "description": "任务归属测试",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = owner_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "归属校验需求",
            "purpose": "验证任务创建归属",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )

    response = other_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_response.json()["id"],
            "config": {"model": "Qwen-2.5-72B"},
        },
    )
    assert response.status_code == 403


def test_aggregator_cannot_update_or_register_artifact_for_foreign_task(
    authenticated_client,
) -> None:
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "外部任务测试集",
            "data_type": "text",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "300 条",
            "sensitivity_level": "internal",
            "description": "任务操作归属测试",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = owner_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "外部任务需求",
            "purpose": "验证任务操作归属",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    task_response = owner_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_response.json()["id"],
            "config": {"model": "Qwen-2.5-72B"},
        },
    )
    task_id = task_response.json()["id"]

    status_response = other_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "越权推进"},
    )
    assert status_response.status_code == 403

    owner_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始处理"},
    )
    owner_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed", "note": "已完成"},
    )

    artifact_disk_path = (
        Path(settings.upload_root) / "processed" / str(task_id) / "foreign-check.jsonl"
    )
    artifact_disk_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_disk_path.write_text('{"ok": true}\n', encoding="utf-8")

    artifact_response = other_client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": artifact_disk_path.name,
            "file_path": f"uploads/processed/{task_id}/foreign-check.jsonl",
            "sample_count": 10,
            "note": "越权登记",
        },
    )
    assert artifact_response.status_code == 403


def test_aggregator_only_sees_own_tasks(authenticated_client) -> None:
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "任务列表测试集",
            "data_type": "text",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "300 条",
            "sensitivity_level": "internal",
            "description": "任务列表过滤测试",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = owner_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "任务列表需求",
            "purpose": "验证 tasks list",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    task_response = owner_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_response.json()["id"],
            "config": {"model": "Qwen-2.5-72B"},
        },
    )
    task_id = task_response.json()["id"]

    owner_list_response = owner_client.get("/api/tasks")
    assert owner_list_response.status_code == 200
    assert owner_list_response.json()[0]["id"] == task_id

    other_list_response = other_client.get("/api/tasks")
    assert other_list_response.status_code == 200
    assert other_list_response.json() == []
