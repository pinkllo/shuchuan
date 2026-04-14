from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.asset import UploadedAsset
from app.db.models.catalog import Catalog, CatalogStatus
from app.db.models.catalog_asset import CatalogAsset
from app.db.models.demand import Demand, DemandStatus
from app.db.models.user import User, UserRole
from app.services.file_storage import save_demand_upload
from app.services.operation_log_service import log_operation


def create_demand(db: Session, *, payload, requester_id: int) -> Demand:
    catalog = db.get(Catalog, payload.catalog_id)
    if catalog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录不存在")
    if catalog.status != CatalogStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录未发布")
    demand = Demand(
        catalog_id=payload.catalog_id,
        requester_id=requester_id,
        provider_id=catalog.provider_id,
        title=payload.title,
        purpose=payload.purpose,
        delivery_plan=payload.delivery_plan,
        status=DemandStatus.PENDING_APPROVAL,
    )
    db.add(demand)
    db.commit()
    db.refresh(demand)
    return demand


def list_demands_for_user(db: Session, *, user: User) -> list[Demand]:
    query = db.query(Demand)
    if user.role == UserRole.PROVIDER:
        query = query.filter(Demand.provider_id == user.id)
    elif user.role == UserRole.AGGREGATOR:
        query = query.filter(Demand.requester_id == user.id)
    elif user.role == UserRole.CONSUMER:
        query = query.filter(Demand.status == DemandStatus.DELIVERED)
    else:
        return []
    return query.order_by(Demand.id.desc()).all()


def list_assets_for_user(db: Session, *, demand_id: int, user: User) -> list[UploadedAsset]:
    demand = db.get(Demand, demand_id)
    if demand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不存在")
    if not _can_read_assets(user=user, demand=demand):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return (
        db.query(UploadedAsset)
        .filter(UploadedAsset.demand_id == demand_id)
        .order_by(UploadedAsset.id.desc())
        .all()
    )


def approve_demand(db: Session, *, demand_id: int, review_note: str, provider_id: int) -> Demand:
    demand = _owned_demand(db, demand_id, provider_id)
    if demand.status != DemandStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="需求状态非法")
    if not _catalog_has_assets(db, catalog_id=demand.catalog_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录下无可用文件")
    demand.status = DemandStatus.DATA_UPLOADED
    demand.approval_note = review_note
    log_operation(
        db,
        action="demand.approved",
        target_type="demand",
        target_id=demand.id,
        actor_id=provider_id,
        detail=review_note,
    )
    db.commit()
    db.refresh(demand)
    return demand


def upload_asset(
    db: Session,
    *,
    demand_id: int,
    upload: UploadFile,
    provider_id: int,
) -> UploadedAsset:
    demand = _owned_demand(db, demand_id, provider_id)
    if demand.status not in {DemandStatus.APPROVED, DemandStatus.DATA_UPLOADED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="需求未审批通过")
    stored = save_demand_upload(demand_id=demand_id, upload=upload)
    asset = UploadedAsset(demand_id=demand.id, uploaded_by=provider_id, **stored)
    demand.status = DemandStatus.DATA_UPLOADED
    db.add(asset)
    db.flush()
    log_operation(
        db,
        action="asset.uploaded",
        target_type="uploaded_asset",
        target_id=asset.id,
        actor_id=provider_id,
        detail=asset.file_name,
    )
    db.commit()
    db.refresh(asset)
    return asset


def _owned_demand(db: Session, demand_id: int, provider_id: int) -> Demand:
    demand = db.get(Demand, demand_id)
    if demand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不存在")
    if demand.provider_id != provider_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return demand


def _can_read_assets(*, user: User, demand: Demand) -> bool:
    if user.role == UserRole.PROVIDER:
        return demand.provider_id == user.id
    if user.role == UserRole.AGGREGATOR:
        return demand.requester_id == user.id
    return False


def _catalog_has_assets(db: Session, *, catalog_id: int) -> bool:
    asset = db.query(CatalogAsset.id).filter(CatalogAsset.catalog_id == catalog_id).first()
    return asset is not None
