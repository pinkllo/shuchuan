from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.task import (
    TaskArtifactCreate,
    TaskArtifactRead,
    TaskCreate,
    TaskRead,
    TaskStatusUpdate,
)
from app.services.task_service import (
    create_processing_task,
    create_task_artifact,
    download_task_result,
    list_tasks_for_creator,
    update_task_status,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks_route(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> list[TaskRead]:
    return list_tasks_for_creator(db, creator_id=user.id)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task_route(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> TaskRead:
    return create_processing_task(db, payload=payload, creator_id=user.id)


@router.post("/{task_id}/status", response_model=TaskRead)
def update_task_status_route(
    task_id: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> TaskRead:
    return update_task_status(db, task_id=task_id, payload=payload, operator_id=user.id)


@router.post("/{task_id}/artifacts", response_model=TaskArtifactRead, status_code=status.HTTP_201_CREATED)
def add_artifact_route(
    task_id: int,
    payload: TaskArtifactCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> TaskArtifactRead:
    return create_task_artifact(db, task_id=task_id, payload=payload, operator_id=user.id)


@router.get("/{task_id}/download")
def download_task_result_route(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
):
    return download_task_result(db, task_id=task_id, operator_id=user.id)
