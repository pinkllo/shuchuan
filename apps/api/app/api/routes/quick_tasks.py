from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.quick_task import QuickTaskCreate, QuickTaskRead
from app.services.quick_task_service import create_quick_task, list_quick_tasks

router = APIRouter(prefix="/api/quick-tasks", tags=["quick-tasks"])


@router.get("", response_model=list[QuickTaskRead])
def list_quick_tasks_route(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> list[QuickTaskRead]:
    return list_quick_tasks(db, creator_id=user.id)


@router.post("", response_model=QuickTaskRead, status_code=status.HTTP_201_CREATED)
def create_quick_task_route(
    payload: QuickTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> QuickTaskRead:
    from app.db.models.demand import Demand
    from app.db.models.catalog import Catalog

    task = create_quick_task(
        db,
        catalog_id=payload.catalog_id,
        input_asset_ids=payload.input_asset_ids,
        task_type=payload.task_type,
        config=payload.config,
        creator_id=user.id,
    )

    # Build response with catalog info
    demand = db.get(Demand, task.demand_id)
    catalog = db.get(Catalog, demand.catalog_id) if demand else None

    return QuickTaskRead(
        id=task.id,
        demand_id=task.demand_id,
        catalog_id=demand.catalog_id if demand else 0,
        catalog_name=catalog.name if catalog else "未知",
        input_asset_ids=[ia.catalog_asset_id for ia in task.input_assets],
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        note=task.note,
        processor_id=task.processor_id,
        processor_name=task.processor.name if task.processor else None,
        created_at=task.created_at,
    )
