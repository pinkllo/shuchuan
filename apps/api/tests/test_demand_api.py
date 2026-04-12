from io import BytesIO


def test_aggregator_can_create_demand_for_published_catalog(
    authenticated_client,
) -> None:
    provider_client = authenticated_client("provider")
    client = authenticated_client("aggregator")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "课程论坛问答集",
            "data_type": "text",
            "granularity": "主题/帖子/回复",
            "version": "v2026.04",
            "fields_description": "标题、正文、回复内容",
            "scale_description": "约 12000 条",
            "sensitivity_level": "internal",
            "description": "教育问答语料",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    response = client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "教育问答清洗需求",
            "purpose": "构造问答训练样本",
            "delivery_plan": "2026-05-31",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending_approval"


def test_provider_can_only_upload_after_approval(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

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
    create_demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "科研摘要清洗需求",
            "purpose": "做指令生成前清洗",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = create_demand_response.json()["id"]

    denied_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    assert denied_response.status_code == 409

    approve_response = provider_client.post(
        f"/api/demands/{demand_id}/approve",
        json={"review_note": "通过"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    upload_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["file_name"] == "sample.jsonl"
    assert upload_response.json()["file_path"].startswith("uploads/raw/")


def test_requester_can_list_uploaded_assets_for_owned_demand(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "资产查询目录",
            "data_type": "text",
            "granularity": "项目/摘要",
            "version": "v1",
            "fields_description": "项目名、摘要",
            "scale_description": "3200 条",
            "sensitivity_level": "internal",
            "description": "资产查询测试",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    create_demand_response = owner_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "资产查询需求",
            "purpose": "为任务创建选择输入资产",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = create_demand_response.json()["id"]

    provider_client.post(
        f"/api/demands/{demand_id}/approve",
        json={"review_note": "通过"},
    )
    provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b'{"ok": true}'), "application/json")},
    )

    owner_response = owner_client.get(f"/api/demands/{demand_id}/assets")
    assert owner_response.status_code == 200
    assert owner_response.json()[0]["demand_id"] == demand_id

    provider_response = provider_client.get(f"/api/demands/{demand_id}/assets")
    assert provider_response.status_code == 200
    assert provider_response.json()[0]["file_name"] == "sample.jsonl"

    forbidden_response = other_client.get(f"/api/demands/{demand_id}/assets")
    assert forbidden_response.status_code == 403


def test_demands_list_is_filtered_by_role(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    owner_client = authenticated_client("aggregator")
    other_aggregator_client = authenticated_client("aggregator")
    consumer_client = authenticated_client("consumer")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "需求列表测试目录",
            "data_type": "text",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "500 条",
            "sensitivity_level": "internal",
            "description": "需求列表过滤测试",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    create_demand_response = owner_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "需求列表测试",
            "purpose": "验证按角色过滤",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = create_demand_response.json()["id"]

    provider_list_response = provider_client.get("/api/demands")
    assert provider_list_response.status_code == 200
    assert provider_list_response.json()[0]["id"] == demand_id

    owner_list_response = owner_client.get("/api/demands")
    assert owner_list_response.status_code == 200
    assert owner_list_response.json()[0]["id"] == demand_id

    other_list_response = other_aggregator_client.get("/api/demands")
    assert other_list_response.status_code == 200
    assert other_list_response.json() == []

    consumer_list_response = consumer_client.get("/api/demands")
    assert consumer_list_response.status_code == 200
    assert consumer_list_response.json() == []


def test_consumer_only_sees_delivered_demands_in_list(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    consumer_client = authenticated_client("consumer")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "交付需求目录",
            "data_type": "text",
            "granularity": "章节/问答",
            "version": "v1",
            "fields_description": "章节、问题、答案",
            "scale_description": "1000 条",
            "sensitivity_level": "internal",
            "description": "consumer demand list",
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "已交付需求",
            "purpose": "验证 consumer demand list",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    upload_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b"{}"), "application/json")},
    )
    task_response = aggregator_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": upload_response.json()["id"],
            "config": {"model": "Qwen-2.5-72B"},
        },
    )
    task_id = task_response.json()["id"]
    aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始"},
    )
    aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed", "note": "完成"},
    )

    from pathlib import Path

    from app.core.config import settings

    artifact_disk_path = Path(settings.upload_root) / "delivery" / str(demand_id) / "delivered.jsonl"
    artifact_disk_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_disk_path.write_text('{"ok": true}\n', encoding="utf-8")

    aggregator_client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": artifact_disk_path.name,
            "file_path": f"uploads/delivery/{demand_id}/delivered.jsonl",
            "sample_count": 10,
            "note": "交付产物",
        },
    )

    response = consumer_client.get("/api/demands")
    assert response.status_code == 200
    assert response.json()[0]["id"] == demand_id
    assert response.json()[0]["status"] == "delivered"
