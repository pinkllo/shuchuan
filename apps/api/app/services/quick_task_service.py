"""Quick-task: one-step demand+task creation for aggregators."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.db.models.catalog import Catalog, CatalogStatus
from app.db.models.catalog_asset import CatalogAsset
from app.db.models.demand import Demand, DemandStatus
from app.db.models.task import ProcessingTask, TaskInputAsset, TaskStatus
from app.schemas.quick_task import QuickTaskRead
from app.services.dispatch_service import try_dispatch
from app.services.operation_log_service import log_operation
from app.services.processor_service import get_dispatch_processor


def create_quick_task(
    db: Session,
    *,
    catalog_id: int,
    input_asset_ids: list[int],
    task_type: str,
    config: dict[str, str],
    creator_id: int,
) -> ProcessingTask:
    """Create demand (auto-approved) + processing task in one step."""
    catalog = db.get(Catalog, catalog_id)
    if catalog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录不存在")
    if catalog.status != CatalogStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录未发布")

    # Validate assets belong to catalog
    asset_ids = list(input_asset_ids)
    if len(set(asset_ids)) != len(asset_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="输入文件不能重复",
        )
    existing = (
        db.query(CatalogAsset.id)
        .filter(CatalogAsset.catalog_id == catalog_id, CatalogAsset.id.in_(asset_ids))
        .all()
    )
    found_ids = {row[0] for row in existing}
    if found_ids != set(asset_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分输入文件不存在")

    # Auto-create demand (skip approval step)
    demand = Demand(
        catalog_id=catalog_id,
        requester_id=creator_id,
        provider_id=catalog.provider_id,
        title=f"{catalog.name} - {task_type}",
        purpose="快速提交",
        delivery_plan="自动",
        status=DemandStatus.PROCESSING,
    )
    db.add(demand)
    db.flush()

    log_operation(
        db,
        action="demand.quick_created",
        target_type="demand",
        target_id=demand.id,
        actor_id=creator_id,
        detail=f"快速创建需求: {catalog.name}",
    )

    # Create processing task
    processor = get_dispatch_processor(db, task_type=task_type)
    task = ProcessingTask(
        demand_id=demand.id,
        created_by=creator_id,
        task_type=task_type,
        status=TaskStatus.QUEUED,
        config_json=config,
    )
    db.add(task)
    db.flush()

    for asset_id in asset_ids:
        db.add(TaskInputAsset(task_id=task.id, catalog_asset_id=asset_id))

    if processor is not None:
        try_dispatch(db, task=task, input_asset_ids=asset_ids, processor=processor)

    log_operation(
        db,
        action="task.quick_created",
        target_type="processing_task",
        target_id=task.id,
        actor_id=creator_id,
        detail=f"快速创建任务: {task_type}",
    )

    db.commit()
    db.refresh(task)
    return task


def list_quick_tasks(db: Session, *, creator_id: int) -> list[QuickTaskRead]:
    """Return a flat list of tasks with catalog info for the aggregator dashboard."""
    tasks = (
        db.query(ProcessingTask)
        .options(
            selectinload(ProcessingTask.input_assets),
            selectinload(ProcessingTask.processor),
        )
        .filter(ProcessingTask.created_by == creator_id)
        .order_by(ProcessingTask.id.desc())
        .all()
    )

    demand_ids = {t.demand_id for t in tasks}
    demands = db.query(Demand).filter(Demand.id.in_(demand_ids)).all() if demand_ids else []
    demand_map = {d.id: d for d in demands}

    catalog_ids = {d.catalog_id for d in demands}
    catalogs = db.query(Catalog).filter(Catalog.id.in_(catalog_ids)).all() if catalog_ids else []
    catalog_map = {c.id: c for c in catalogs}

    result = []
    for task in tasks:
        demand = demand_map.get(task.demand_id)
        catalog = catalog_map.get(demand.catalog_id) if demand else None
        result.append(
            QuickTaskRead(
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
        )
    return result
