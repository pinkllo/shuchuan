import logging
from pathlib import Path, PurePosixPath

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.catalog_asset import CatalogAsset
from app.db.models.processor import Processor
from app.db.models.task import ProcessingTask, TaskStatus

CALLBACK_BASE_URL = "http://localhost:8000"
DISPATCH_TIMEOUT_SECONDS = 10
DELIVERY_DIR_NAME = "delivery"
UPLOADS_DIR_NAME = "uploads"

logger = logging.getLogger(__name__)


def try_dispatch(
    db: Session,
    *,
    task: ProcessingTask,
    input_asset_ids: list[int],
    processor: Processor,
) -> None:
    assets = db.query(CatalogAsset).filter(CatalogAsset.id.in_(input_asset_ids)).all()
    payload = _build_dispatch_payload(task=task, assets=assets)
    try:
        response = httpx.post(
            f"{processor.endpoint_url}/execute",
            json=payload,
            headers={"Authorization": f"Bearer {processor.api_token}"},
            timeout=DISPATCH_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        task.note = f"自动派发失败: {exc}"
        logger.warning("Task %s dispatch failed: %s", task.id, exc)
        return
    if response.status_code != 202:
        task.note = f"自动派发失败: 处理器返回 {response.status_code}"
        logger.warning(
            "Task %s dispatch rejected by processor %s with status %s",
            task.id,
            processor.name,
            response.status_code,
        )
        return
    task.status = TaskStatus.RUNNING
    task.processor_id = processor.id
    logger.info("Task %s dispatched to processor %s", task.id, processor.name)


def _build_dispatch_payload(
    *,
    task: ProcessingTask,
    assets: list[CatalogAsset],
) -> dict[str, object]:
    upload_root = Path(settings.upload_root).resolve()
    output_dir = upload_root / DELIVERY_DIR_NAME / f"task_{task.id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "task_id": task.id,
        "task_type": task.task_type,
        "callback_base_url": CALLBACK_BASE_URL,
        "input_files": [_map_asset(asset, upload_root) for asset in assets],
        "config": task.config_json or {},
        "output_dir": str(output_dir),
    }


def _map_asset(asset: CatalogAsset, upload_root: Path) -> dict[str, object]:
    relative_path = PurePosixPath(asset.file_path)
    absolute_path = upload_root.joinpath(*relative_path.parts[1:])
    return {
        "asset_id": asset.id,
        "file_name": asset.file_name,
        "file_path": str(absolute_path),
    }
