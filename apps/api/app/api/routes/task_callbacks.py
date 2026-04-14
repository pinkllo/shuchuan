from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.processor_auth import authenticate_processor
from app.db.models.demand import Demand, DemandStatus
from app.db.models.processor import Processor
from app.db.models.task import ProcessingTask, TaskArtifact, TaskStatus
from app.schemas.processor import TaskCompleteReport, TaskFailReport, TaskProgressReport
from app.services.file_storage import ensure_existing_upload
from app.services.operation_log_service import log_operation

ARTIFACT_TYPE = "processor_output"

router = APIRouter(prefix="/api/tasks", tags=["task-callbacks"])


@router.post("/{task_id}/progress")
def report_progress(
    task_id: int,
    payload: TaskProgressReport,
    db: Session = Depends(get_db),
    processor: Processor = Depends(authenticate_processor),
) -> dict[str, int | str]:
    task = _get_task_for_processor(db, task_id=task_id, processor=processor)
    task.progress = payload.progress
    if payload.message:
        task.note = payload.message
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "progress": task.progress, "status": task.status.value}


@router.post("/{task_id}/complete")
def report_complete(
    task_id: int,
    payload: TaskCompleteReport,
    db: Session = Depends(get_db),
    processor: Processor = Depends(authenticate_processor),
) -> dict[str, int | str]:
    task = _get_task_for_processor(db, task_id=task_id, processor=processor)
    task.status = TaskStatus.COMPLETED
    task.progress = 100
    if payload.message:
        task.note = payload.message
    _create_artifacts(db, task=task, payload=payload)
    _mark_demand_delivered(db, task=task, payload=payload)
    log_operation(
        db,
        action="task.completed_by_processor",
        target_type="processing_task",
        target_id=task.id,
        detail=payload.message,
    )
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "status": task.status.value, "progress": task.progress}


@router.post("/{task_id}/fail")
def report_fail(
    task_id: int,
    payload: TaskFailReport,
    db: Session = Depends(get_db),
    processor: Processor = Depends(authenticate_processor),
) -> dict[str, int | str]:
    task = _get_task_for_processor(db, task_id=task_id, processor=processor)
    task.status = TaskStatus.FAILED
    task.note = _build_failure_note(payload)
    log_operation(
        db,
        action="task.failed_by_processor",
        target_type="processing_task",
        target_id=task.id,
        detail=task.note,
    )
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "status": task.status.value}


def _get_task_for_processor(
    db: Session,
    *,
    task_id: int,
    processor: Processor,
) -> ProcessingTask:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    if task.processor_id != processor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此任务",
        )
    return task


def _create_artifacts(
    db: Session,
    *,
    task: ProcessingTask,
    payload: TaskCompleteReport,
) -> None:
    for output_file in payload.output_files:
        ensure_existing_upload(output_file.file_path)
        db.add(
            TaskArtifact(
                task_id=task.id,
                artifact_type=ARTIFACT_TYPE,
                file_name=output_file.file_name,
                file_path=output_file.file_path,
                sample_count=output_file.sample_count,
                note=payload.message or None,
            )
        )


def _mark_demand_delivered(
    db: Session,
    *,
    task: ProcessingTask,
    payload: TaskCompleteReport,
) -> None:
    if not any(item.file_path.startswith("uploads/delivery/") for item in payload.output_files):
        return
    demand = db.get(Demand, task.demand_id)
    if demand is not None:
        demand.status = DemandStatus.DELIVERED


def _build_failure_note(payload: TaskFailReport) -> str:
    if not payload.message:
        return payload.error
    return f"{payload.error}: {payload.message}"
