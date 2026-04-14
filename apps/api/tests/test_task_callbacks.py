from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.catalog import Catalog, CatalogStatus
from app.db.models.catalog_asset import CatalogAsset
from app.db.models.demand import Demand, DemandStatus
from app.db.models.task import ProcessingTask, TaskInputAsset, TaskStatus
from app.db.models.user import User


def _register_processor(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/processors/register",
        json={
            "name": "test-proc",
            "task_type": "instruction",
            "description": "test",
            "endpoint_url": "http://localhost:9999",
        },
    )
    assert response.status_code == 201
    return response.json()


def _seed_catalog(db_session: Session, *, provider_id: int) -> Catalog:
    catalog = Catalog(
        provider_id=provider_id,
        name="test",
        data_type="text",
        granularity="doc",
        version="1.0",
        fields_description="f",
        scale_description="s",
        upload_method="batch",
        sensitivity_level="low",
        description="d",
        status=CatalogStatus.PUBLISHED,
    )
    db_session.add(catalog)
    db_session.flush()
    return catalog


def _seed_task(
    db_session: Session,
    *,
    demand_id: int,
    created_by: int,
    processor_id: int,
    asset_id: int,
) -> ProcessingTask:
    task = ProcessingTask(
        demand_id=demand_id,
        created_by=created_by,
        task_type="instruction",
        status=TaskStatus.RUNNING,
        config_json={},
        processor_id=processor_id,
    )
    db_session.add(task)
    db_session.flush()
    db_session.add(TaskInputAsset(task_id=task.id, catalog_asset_id=asset_id))
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture()
def processor_and_task(
    client: TestClient,
    authenticated_client,
    db_session: Session,
) -> Iterator[dict[str, int | str]]:
    processor_data = _register_processor(client)
    authenticated_client("provider")
    authenticated_client("aggregator")
    provider_user = db_session.query(User).filter(User.username.like("provider%")).first()
    aggregator_user = db_session.query(User).filter(User.username.like("aggregator%")).first()
    assert provider_user is not None
    assert aggregator_user is not None

    catalog = _seed_catalog(db_session, provider_id=provider_user.id)
    asset = CatalogAsset(
        catalog_id=catalog.id,
        uploaded_by=provider_user.id,
        file_name="test.txt",
        file_path=f"uploads/catalogs/{catalog.id}/test.txt",
        file_size=100,
        file_type="text/plain",
    )
    db_session.add(asset)
    db_session.flush()
    demand = Demand(
        catalog_id=catalog.id,
        requester_id=aggregator_user.id,
        provider_id=provider_user.id,
        title="test demand",
        purpose="test",
        delivery_plan="online",
        status=DemandStatus.DATA_UPLOADED,
    )
    db_session.add(demand)
    db_session.flush()
    task = _seed_task(
        db_session,
        demand_id=demand.id,
        created_by=aggregator_user.id,
        processor_id=int(processor_data["processor_id"]),
        asset_id=asset.id,
    )

    yield {
        "api_token": str(processor_data["api_token"]),
        "task_id": task.id,
        "demand_id": demand.id,
    }


def test_progress(client: TestClient, processor_and_task: dict[str, int | str]) -> None:
    response = client.post(
        f"/api/tasks/{processor_and_task['task_id']}/progress",
        json={"progress": 50, "message": "half done"},
        headers={"Authorization": f"Bearer {processor_and_task['api_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["progress"] == 50


def test_complete(client: TestClient, processor_and_task: dict[str, int | str]) -> None:
    output_dir = Path(settings.upload_root) / "delivery" / f"task_{processor_and_task['task_id']}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "result.json"
    output_file.write_text("{}", encoding="utf-8")

    response = client.post(
        f"/api/tasks/{processor_and_task['task_id']}/complete",
        json={
            "output_files": [
                {
                    "file_path": f"uploads/delivery/task_{processor_and_task['task_id']}/result.json",
                    "file_name": "result.json",
                    "sample_count": 100,
                }
            ],
            "message": "done",
        },
        headers={"Authorization": f"Bearer {processor_and_task['api_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_fail(client: TestClient, processor_and_task: dict[str, int | str]) -> None:
    response = client.post(
        f"/api/tasks/{processor_and_task['task_id']}/fail",
        json={"error": "format error", "message": "unsupported file"},
        headers={"Authorization": f"Bearer {processor_and_task['api_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_callback_rejects_wrong_token(
    client: TestClient,
    processor_and_task: dict[str, int | str],
) -> None:
    response = client.post(
        f"/api/tasks/{processor_and_task['task_id']}/progress",
        json={"progress": 10, "message": "test"},
        headers={"Authorization": "Bearer sp_wrong"},
    )

    assert response.status_code == 403
