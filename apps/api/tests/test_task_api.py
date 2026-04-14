from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table

from app.core.config import settings
from app.db.models.demand import Demand, DemandStatus

CATALOG_ASSETS = Table(
    "catalog_assets",
    MetaData(),
    Column("id", Integer, primary_key=True),
    Column("catalog_id", Integer, nullable=False),
    Column("uploaded_by", Integer, nullable=False),
    Column("file_name", String(255), nullable=False),
    Column("file_path", String(255), nullable=False),
    Column("file_size", Integer, nullable=False),
    Column("file_type", String(128), nullable=False),
    Column("uploaded_at", DateTime(timezone=True), nullable=False),
)


def _catalog_payload(name: str) -> dict[str, str]:
    return {
        "name": name,
        "data_type": "text",
        "granularity": "主题/帖子",
        "version": "v1",
        "fields_description": "标题、正文",
        "scale_description": "300 条",
        "upload_method": "平台上传",
        "sensitivity_level": "internal",
        "description": f"{name}描述",
    }


def _catalog_files(*names: str) -> list[tuple[str, tuple[str, BytesIO, str]]]:
    return [
        ("files", (name, BytesIO(b'{"ok": true}\n'), "application/json"))
        for name in names
    ]


def _create_catalog(provider_client, *, name: str) -> int:
    response = provider_client.post(
        "/api/catalogs",
        data=_catalog_payload(name),
        files=_catalog_files(f"{name}.jsonl"),
    )
    assert response.status_code == 201
    catalog_id = response.json()["id"]
    publish_response = provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    assert publish_response.status_code == 200
    return catalog_id


def _create_demand(provider_client, aggregator_client, *, catalog_id: int, title: str) -> int:
    response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": title,
            "purpose": f"{title}用途",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    return demand_id


def _prepare_task_context(db_session, provider_client, aggregator_client, *, name: str) -> Demand:
    catalog_id = _create_catalog(provider_client, name=name)
    demand_id = _create_demand(
        provider_client,
        aggregator_client,
        catalog_id=catalog_id,
        title=f"{name}需求",
    )
    demand = db_session.get(Demand, demand_id)
    demand.status = DemandStatus.DATA_UPLOADED
    db_session.commit()
    return demand


def _seed_catalog_assets(db_session, *, catalog_id: int, uploaded_by: int, count: int = 2) -> list[int]:
    CATALOG_ASSETS.create(bind=db_session.bind, checkfirst=True)
    asset_ids: list[int] = []
    for index in range(count):
        result = db_session.execute(
            CATALOG_ASSETS.insert().values(
                catalog_id=catalog_id,
                uploaded_by=uploaded_by,
                file_name=f"asset-{catalog_id}-{index}.jsonl",
                file_path=f"uploads/catalogs/{catalog_id}/asset-{index}.jsonl",
                file_size=2,
                file_type="application/json",
                uploaded_at=datetime.now(timezone.utc),
            )
        )
        asset_ids.append(result.inserted_primary_key[0])
    db_session.commit()
    return asset_ids


def _task_payload(demand_id: int, input_asset_ids: list[int]) -> dict[str, object]:
    return {
        "demand_id": demand_id,
        "input_asset_ids": input_asset_ids,
        "task_type": "instruction",
        "config": {
            "model": "Qwen-2.5-72B",
            "prompt_template": "标准问答模板",
            "batch_size": "32",
        },
    }


def _create_task(client, *, demand_id: int, input_asset_ids: list[int]) -> int:
    response = client.post("/api/tasks", json=_task_payload(demand_id, input_asset_ids))
    assert response.status_code == 201
    return response.json()["id"]


def test_aggregator_can_create_task_with_multiple_catalog_assets(
    authenticated_client,
    db_session,
) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    demand = _prepare_task_context(
        db_session,
        provider_client,
        aggregator_client,
        name="科研摘要多文件",
    )
    asset_ids = _seed_catalog_assets(
        db_session,
        catalog_id=demand.catalog_id,
        uploaded_by=demand.provider_id,
    )

    response = aggregator_client.post("/api/tasks", json=_task_payload(demand.id, asset_ids))

    assert response.status_code == 201
    assert response.json()["status"] == "queued"
    assert response.json()["input_asset_ids"] == asset_ids
    assert db_session.get(Demand, demand.id).status == DemandStatus.PROCESSING


def test_task_rejects_catalog_asset_outside_demand_catalog(authenticated_client, db_session) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    demand = _prepare_task_context(
        db_session,
        provider_client,
        aggregator_client,
        name="目录归属校验",
    )
    valid_asset_id = _seed_catalog_assets(
        db_session,
        catalog_id=demand.catalog_id,
        uploaded_by=demand.provider_id,
        count=1,
    )[0]
    foreign_catalog_id = _create_catalog(provider_client, name="外部目录")
    foreign_asset_id = _seed_catalog_assets(
        db_session,
        catalog_id=foreign_catalog_id,
        uploaded_by=demand.provider_id,
        count=1,
    )[0]

    response = aggregator_client.post(
        "/api/tasks",
        json=_task_payload(demand.id, [valid_asset_id, foreign_asset_id]),
    )

    assert response.status_code == 409


def test_task_rejects_duplicate_catalog_asset_ids(authenticated_client, db_session) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    demand = _prepare_task_context(
        db_session,
        provider_client,
        aggregator_client,
        name="重复文件校验",
    )
    asset_id = _seed_catalog_assets(
        db_session,
        catalog_id=demand.catalog_id,
        uploaded_by=demand.provider_id,
        count=1,
    )[0]

    response = aggregator_client.post(
        "/api/tasks",
        json=_task_payload(demand.id, [asset_id, asset_id]),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "输入文件不能重复"


def test_task_can_transition_to_completed_with_artifact(authenticated_client, db_session) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    demand = _prepare_task_context(
        db_session,
        provider_client,
        aggregator_client,
        name="教育问答任务",
    )
    task_id = _create_task(
        aggregator_client,
        demand_id=demand.id,
        input_asset_ids=_seed_catalog_assets(
            db_session,
            catalog_id=demand.catalog_id,
            uploaded_by=demand.provider_id,
        ),
    )

    assert aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始处理"},
    ).status_code == 200
    assert aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed", "note": "已完成"},
    ).status_code == 200

    artifact_disk_path = Path(settings.upload_root) / "processed" / str(task_id) / "instruction.jsonl"
    artifact_disk_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_disk_path.write_text('{"ok": true}\n', encoding="utf-8")

    response = aggregator_client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": artifact_disk_path.name,
            "file_path": f"uploads/processed/{task_id}/instruction.jsonl",
            "sample_count": 1200,
            "note": "一期半接入产物登记",
        },
    )
    assert response.status_code == 201


def test_failed_task_requires_explicit_reason(authenticated_client, db_session) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    demand = _prepare_task_context(
        db_session,
        provider_client,
        aggregator_client,
        name="失败原因校验",
    )
    task_id = _create_task(
        aggregator_client,
        demand_id=demand.id,
        input_asset_ids=_seed_catalog_assets(
            db_session,
            catalog_id=demand.catalog_id,
            uploaded_by=demand.provider_id,
            count=1,
        ),
    )
    aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "开始处理"},
    )

    invalid_response = aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "failed", "note": ""},
    )
    failed_response = aggregator_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "failed", "note": "模型调用失败"},
    )

    assert invalid_response.status_code == 422
    assert failed_response.status_code == 200
    assert failed_response.json()["status"] == "failed"
    assert failed_response.json()["note"] == "模型调用失败"


def test_aggregator_cannot_create_task_for_other_requester_demand(
    authenticated_client,
    db_session,
) -> None:
    provider_client = authenticated_client("provider")
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")
    demand = _prepare_task_context(db_session, provider_client, owner_client, name="归属校验")
    asset_ids = _seed_catalog_assets(
        db_session,
        catalog_id=demand.catalog_id,
        uploaded_by=demand.provider_id,
    )

    response = other_client.post("/api/tasks", json=_task_payload(demand.id, asset_ids))

    assert response.status_code == 403


def test_aggregator_cannot_update_or_register_artifact_for_foreign_task(
    authenticated_client,
    db_session,
) -> None:
    provider_client = authenticated_client("provider")
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")
    demand = _prepare_task_context(db_session, provider_client, owner_client, name="任务操作归属")
    task_id = _create_task(
        owner_client,
        demand_id=demand.id,
        input_asset_ids=_seed_catalog_assets(
            db_session,
            catalog_id=demand.catalog_id,
            uploaded_by=demand.provider_id,
        ),
    )

    assert other_client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "running", "note": "越权推进"},
    ).status_code == 403
    owner_client.post(f"/api/tasks/{task_id}/status", json={"status": "running", "note": "开始处理"})
    owner_client.post(f"/api/tasks/{task_id}/status", json={"status": "completed", "note": "已完成"})

    artifact_disk_path = Path(settings.upload_root) / "processed" / str(task_id) / "foreign.jsonl"
    artifact_disk_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_disk_path.write_text('{"ok": true}\n', encoding="utf-8")

    response = other_client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": artifact_disk_path.name,
            "file_path": f"uploads/processed/{task_id}/foreign.jsonl",
            "sample_count": 10,
            "note": "越权登记",
        },
    )
    assert response.status_code == 403


def test_aggregator_only_sees_own_tasks(authenticated_client, db_session) -> None:
    provider_client = authenticated_client("provider")
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")
    demand = _prepare_task_context(db_session, provider_client, owner_client, name="任务列表")
    asset_ids = _seed_catalog_assets(
        db_session,
        catalog_id=demand.catalog_id,
        uploaded_by=demand.provider_id,
    )
    task_id = _create_task(owner_client, demand_id=demand.id, input_asset_ids=asset_ids)

    owner_response = owner_client.get("/api/tasks")
    other_response = other_client.get("/api/tasks")

    assert owner_response.status_code == 200
    assert owner_response.json()[0]["id"] == task_id
    assert owner_response.json()[0]["input_asset_ids"] == asset_ids
    assert other_response.status_code == 200
    assert other_response.json() == []
