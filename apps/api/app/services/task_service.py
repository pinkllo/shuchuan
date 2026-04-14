from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session, selectinload

from app.db.models.demand import Demand, DemandStatus
from app.db.models.task import ProcessingTask, TaskArtifact, TaskInputAsset, TaskStatus
from app.schemas.delivery import DeliveryRead
from app.services.file_storage import ensure_existing_upload
from app.services.operation_log_service import log_operation

ALLOWED_TRANSITIONS = {
    TaskStatus.QUEUED: {TaskStatus.RUNNING},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED},
}
ACTIVE_DEMAND_STATUSES = {DemandStatus.DATA_UPLOADED, DemandStatus.PROCESSING}
CATALOG_ASSET_LOOKUP = text(
    "SELECT id, catalog_id FROM catalog_assets WHERE id IN :asset_ids"
).bindparams(bindparam("asset_ids", expanding=True))


def create_processing_task(db: Session, *, payload, creator_id: int) -> ProcessingTask:
    demand = db.get(Demand, payload.demand_id)
    _ensure_task_access(demand, creator_id=creator_id)
    _ensure_demand_ready(demand)
    asset_ids = _validate_catalog_assets(
        db,
        catalog_id=demand.catalog_id,
        input_asset_ids=payload.input_asset_ids,
    )
    task = ProcessingTask(
        demand_id=payload.demand_id,
        created_by=creator_id,
        task_type=payload.task_type,
        status=TaskStatus.QUEUED,
        config_json=payload.config,
    )
    demand.status = DemandStatus.PROCESSING
    db.add(task)
    db.flush()
    for asset_id in asset_ids:
        db.add(TaskInputAsset(task_id=task.id, catalog_asset_id=asset_id))
    db.commit()
    db.refresh(task)
    return task


def list_tasks_for_creator(db: Session, *, creator_id: int) -> list[ProcessingTask]:
    return (
        db.query(ProcessingTask)
        .options(selectinload(ProcessingTask.input_assets))
        .filter(ProcessingTask.created_by == creator_id)
        .order_by(ProcessingTask.id.desc())
        .all()
    )


def update_task_status(db: Session, *, task_id: int, payload, operator_id: int) -> ProcessingTask:
    task = _get_task(db, task_id, operator_id=operator_id)
    if payload.status not in ALLOWED_TRANSITIONS.get(task.status, set()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="任务状态非法")
    task.status = payload.status
    task.note = payload.note
    task.progress = 100 if payload.status == TaskStatus.COMPLETED else task.progress
    log_operation(
        db,
        action="task.status_updated",
        target_type="processing_task",
        target_id=task.id,
        actor_id=operator_id,
        detail=payload.note,
    )
    db.commit()
    db.refresh(task)
    return task


def create_task_artifact(db: Session, *, task_id: int, payload, operator_id: int) -> TaskArtifact:
    task = _get_task(db, task_id, operator_id=operator_id)
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="任务未完成")
    ensure_existing_upload(payload.file_path)
    artifact = TaskArtifact(task_id=task.id, **payload.model_dump())
    db.add(artifact)
    if payload.file_path.startswith("uploads/delivery/"):
        demand = db.get(Demand, task.demand_id)
        if demand is not None:
            demand.status = DemandStatus.DELIVERED
    db.flush()
    log_operation(
        db,
        action="task.artifact_registered",
        target_type="task_artifact",
        target_id=artifact.id,
        actor_id=operator_id,
        detail=artifact.file_name,
    )
    db.commit()
    db.refresh(artifact)
    return artifact


def list_deliveries(db: Session) -> list[DeliveryRead]:
    artifacts = (
        db.query(TaskArtifact, Demand)
        .join(ProcessingTask, TaskArtifact.task_id == ProcessingTask.id)
        .join(Demand, ProcessingTask.demand_id == Demand.id)
        .filter(Demand.status == DemandStatus.DELIVERED)
        .filter(TaskArtifact.file_path.like("uploads/delivery/%"))
        .order_by(TaskArtifact.created_at.desc(), TaskArtifact.id.desc())
        .all()
    )
    return [
        DeliveryRead(
            demand_id=demand.id,
            demand_title=demand.title,
            artifact_file_name=artifact.file_name,
            sample_count=artifact.sample_count,
            delivered_at=artifact.created_at,
        )
        for artifact, demand in artifacts
    ]


def download_delivery(db: Session, *, demand_id: int, consumer_id: int) -> FileResponse:
    artifact = (
        db.query(TaskArtifact)
        .join(ProcessingTask, TaskArtifact.task_id == ProcessingTask.id)
        .filter(ProcessingTask.demand_id == demand_id)
        .filter(TaskArtifact.file_path.like("uploads/delivery/%"))
        .order_by(TaskArtifact.created_at.desc(), TaskArtifact.id.desc())
        .first()
    )
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交付文件不存在")
    file_path = ensure_existing_upload(artifact.file_path)
    log_operation(
        db,
        action="delivery.downloaded",
        target_type="demand",
        target_id=demand_id,
        actor_id=consumer_id,
        detail=artifact.file_name,
    )
    db.commit()
    return FileResponse(path=Path(file_path), filename=artifact.file_name)


def _get_task(db: Session, task_id: int, *, operator_id: int) -> ProcessingTask:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.created_by != operator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return task


def _ensure_task_access(demand: Demand | None, *, creator_id: int) -> None:
    if demand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不存在")
    if demand.requester_id != creator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def _ensure_demand_ready(demand: Demand) -> None:
    if demand.status not in ACTIVE_DEMAND_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="需求尚未上传数据")


def _validate_catalog_assets(
    db: Session,
    *,
    catalog_id: int,
    input_asset_ids: list[int],
) -> list[int]:
    asset_ids = list(input_asset_ids)
    if len(set(asset_ids)) != len(asset_ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="输入文件不能重复")
    asset_catalogs = _load_catalog_assets(db, asset_ids)
    if len(asset_catalogs) != len(set(asset_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务输入不存在")
    if any(asset_catalog != catalog_id for asset_catalog in asset_catalogs.values()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="任务输入不属于当前目录")
    return asset_ids


def _load_catalog_assets(db: Session, asset_ids: list[int]) -> dict[int, int]:
    rows = db.execute(CATALOG_ASSET_LOOKUP, {"asset_ids": asset_ids}).mappings().all()
    return {row["id"]: row["catalog_id"] for row in rows}
