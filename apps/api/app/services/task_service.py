from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.models.asset import UploadedAsset
from app.db.models.demand import Demand, DemandStatus
from app.db.models.task import ProcessingTask, TaskArtifact, TaskStatus
from app.schemas.delivery import DeliveryRead
from app.services.file_storage import ensure_existing_upload
from app.services.operation_log_service import log_operation

ALLOWED_TRANSITIONS = {
    TaskStatus.QUEUED: {TaskStatus.RUNNING},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED},
}


def create_processing_task(db: Session, *, payload, creator_id: int) -> ProcessingTask:
    demand = db.get(Demand, payload.demand_id)
    asset = db.get(UploadedAsset, payload.input_asset_id)
    if demand is None or asset is None or asset.demand_id != payload.demand_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务输入不存在")
    if demand.requester_id != creator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    if demand.status != DemandStatus.DATA_UPLOADED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="需求尚未上传数据")
    task = ProcessingTask(
        demand_id=payload.demand_id,
        input_asset_id=payload.input_asset_id,
        created_by=creator_id,
        task_type=payload.task_type,
        status=TaskStatus.QUEUED,
        config_json=payload.config,
    )
    demand.status = DemandStatus.PROCESSING
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks_for_creator(db: Session, *, creator_id: int) -> list[ProcessingTask]:
    return (
        db.query(ProcessingTask)
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
