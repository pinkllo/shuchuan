from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.catalog import Catalog, CatalogStatus
from app.db.models.catalog_asset import CatalogAsset
from app.db.models.demand import Demand, DemandStatus
from app.db.models.processor import Processor, ProcessorStatus
from app.db.models.user import User


def _seed_catalog_context(
    db_session: Session,
    *,
    provider_id: int,
    requester_id: int,
) -> tuple[Demand, CatalogAsset]:
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
    asset = CatalogAsset(
        catalog_id=catalog.id,
        uploaded_by=provider_id,
        file_name="test.txt",
        file_path=f"uploads/catalogs/{catalog.id}/test.txt",
        file_size=100,
        file_type="text/plain",
    )
    db_session.add(asset)
    db_session.flush()
    demand = Demand(
        catalog_id=catalog.id,
        requester_id=requester_id,
        provider_id=provider_id,
        title="test",
        purpose="test",
        delivery_plan="online",
        status=DemandStatus.DATA_UPLOADED,
    )
    db_session.add(demand)
    db_session.commit()
    db_session.refresh(demand)
    db_session.refresh(asset)
    return demand, asset


def _seed_processor(
    db_session: Session,
    *,
    task_type: str,
    status: ProcessorStatus = ProcessorStatus.ONLINE,
) -> Processor:
    processor = Processor(
        name="auto-proc",
        task_type=task_type,
        description="auto",
        endpoint_url="http://localhost:9999",
        api_token="sp_test_token",
        status=status,
    )
    db_session.add(processor)
    db_session.commit()
    db_session.refresh(processor)
    return processor


@pytest.fixture()
def aggregator_context(
    authenticated_client,
    db_session: Session,
) -> Iterator[dict[str, object]]:
    authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    provider_user = db_session.query(User).filter(User.username.like("provider%")).first()
    aggregator_user = db_session.query(User).filter(User.username.like("aggregator%")).first()
    assert provider_user is not None
    assert aggregator_user is not None
    demand, asset = _seed_catalog_context(
        db_session,
        provider_id=provider_user.id,
        requester_id=aggregator_user.id,
    )
    yield {"client": aggregator_client, "demand": demand, "asset": asset}


def test_task_auto_dispatched_to_processor(
    aggregator_context: dict[str, object],
    db_session: Session,
) -> None:
    _seed_processor(db_session, task_type="instruction")
    response = MagicMock()
    response.status_code = 202
    response.json.return_value = {"accepted": True}
    aggregator_client = aggregator_context["client"]
    demand = aggregator_context["demand"]
    asset = aggregator_context["asset"]

    with patch("app.services.dispatch_service.httpx.post", return_value=response) as post_mock:
        create_response = aggregator_client.post(
            "/api/tasks",
            json={
                "demand_id": demand.id,
                "input_asset_ids": [asset.id],
                "task_type": "instruction",
                "config": {},
            },
        )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "running"
    assert create_response.json()["processor_id"] is not None
    assert post_mock.called


def test_task_keeps_manual_mode_without_processor(
    aggregator_context: dict[str, object],
) -> None:
    aggregator_client = aggregator_context["client"]
    demand = aggregator_context["demand"]
    asset = aggregator_context["asset"]

    response = aggregator_client.post(
        "/api/tasks",
        json={
            "demand_id": demand.id,
            "input_asset_ids": [asset.id],
            "task_type": "unknown_type",
            "config": {},
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "queued"
    assert response.json()["processor_id"] is None


def test_task_rejects_offline_processor(
    aggregator_context: dict[str, object],
    db_session: Session,
) -> None:
    _seed_processor(
        db_session,
        task_type="instruction",
        status=ProcessorStatus.OFFLINE,
    )
    aggregator_client = aggregator_context["client"]
    demand = aggregator_context["demand"]
    asset = aggregator_context["asset"]

    response = aggregator_client.post(
        "/api/tasks",
        json={
            "demand_id": demand.id,
            "input_asset_ids": [asset.id],
            "task_type": "instruction",
            "config": {},
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "处理器离线"
