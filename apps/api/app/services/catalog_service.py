from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from app.db.models.catalog import Catalog, CatalogStatus
from app.db.models.catalog_asset import CatalogAsset
from app.db.models.demand import Demand, DemandStatus
from app.db.models.task import TaskInputAsset
from app.db.models.user import User, UserRole
from app.services.file_storage import delete_upload, ensure_existing_upload, read_text_preview, save_catalog_upload
from app.services.operation_log_service import log_operation

READABLE_DEMAND_STATUSES = (
    DemandStatus.APPROVED,
    DemandStatus.DATA_UPLOADED,
    DemandStatus.PROCESSING,
    DemandStatus.DELIVERED,
)


def create_catalog(db: Session, *, payload, files: list[UploadFile], provider_id: int) -> Catalog:
    _ensure_uploads_present(files)
    catalog = Catalog(provider_id=provider_id, status=CatalogStatus.DRAFT, **payload.model_dump())
    db.add(catalog)
    db.flush()
    _create_catalog_assets(db, catalog_id=catalog.id, files=files, provider_id=provider_id)
    log_operation(
        db,
        action="catalog.created",
        target_type="catalog",
        target_id=catalog.id,
        actor_id=provider_id,
    )
    db.commit()
    return _load_catalog(db, catalog.id)


def publish_catalog(db: Session, *, catalog_id: int, provider_id: int) -> Catalog:
    catalog = _owned_catalog(db, catalog_id, provider_id)
    if catalog.status != CatalogStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录状态非法")
    if not _catalog_has_assets(db, catalog_id=catalog.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录下无可用文件")
    catalog.status = CatalogStatus.PUBLISHED
    log_operation(
        db,
        action="catalog.published",
        target_type="catalog",
        target_id=catalog.id,
        actor_id=provider_id,
    )
    db.commit()
    return _load_catalog(db, catalog.id)


def archive_catalog(db: Session, *, catalog_id: int, provider_id: int) -> Catalog:
    catalog = _owned_catalog(db, catalog_id, provider_id)
    if catalog.status == CatalogStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录状态非法")
    catalog.status = CatalogStatus.ARCHIVED
    log_operation(
        db,
        action="catalog.archived",
        target_type="catalog",
        target_id=catalog.id,
        actor_id=provider_id,
    )
    db.commit()
    return _load_catalog(db, catalog.id)


def list_my_catalogs(db: Session, *, provider_id: int) -> list[Catalog]:
    return (
        db.query(Catalog)
        .options(selectinload(Catalog.assets))
        .filter(Catalog.provider_id == provider_id)
        .order_by(Catalog.id.desc())
        .all()
    )


def list_published_catalogs(db: Session) -> list[Catalog]:
    return (
        db.query(Catalog)
        .options(selectinload(Catalog.assets))
        .filter(Catalog.status == CatalogStatus.PUBLISHED)
        .order_by(Catalog.id.desc())
        .all()
    )


def list_catalog_assets_for_user(db: Session, *, catalog_id: int, user: User) -> list[CatalogAsset]:
    _ensure_catalog_assets_readable(db, catalog_id=catalog_id, user=user)
    return (
        db.query(CatalogAsset)
        .filter(CatalogAsset.catalog_id == catalog_id)
        .order_by(CatalogAsset.id.desc())
        .all()
    )


def preview_catalog_asset_for_user(
    db: Session,
    *,
    catalog_id: int,
    asset_id: int,
    user: User,
) -> dict[str, object]:
    asset = _get_readable_catalog_asset(db, catalog_id=catalog_id, asset_id=asset_id, user=user)
    preview_text, preview_line_count, truncated = read_text_preview(asset.file_path)
    return {
        "asset_id": asset.id,
        "catalog_id": asset.catalog_id,
        "file_name": asset.file_name,
        "file_type": asset.file_type,
        "file_size": asset.file_size,
        "uploaded_at": asset.uploaded_at,
        "preview_text": preview_text,
        "preview_line_count": preview_line_count,
        "truncated": truncated,
    }


def preview_catalog_asset_file_for_user(
    db: Session,
    *,
    catalog_id: int,
    asset_id: int,
    user: User,
) -> FileResponse:
    asset = _get_readable_catalog_asset(db, catalog_id=catalog_id, asset_id=asset_id, user=user)
    file_path = ensure_existing_upload(asset.file_path)
    return FileResponse(
        path=file_path,
        media_type=asset.file_type,
        filename=asset.file_name,
        content_disposition_type="inline",
    )


def add_catalog_assets(
    db: Session,
    *,
    catalog_id: int,
    files: list[UploadFile],
    provider_id: int,
) -> list[CatalogAsset]:
    catalog = _owned_catalog(db, catalog_id, provider_id)
    _ensure_uploads_present(files)
    assets = _create_catalog_assets(db, catalog_id=catalog.id, files=files, provider_id=provider_id)
    db.commit()
    return assets


def delete_catalog_asset(
    db: Session,
    *,
    catalog_id: int,
    asset_id: int,
    provider_id: int,
) -> None:
    _owned_catalog(db, catalog_id, provider_id)
    asset = (
        db.query(CatalogAsset)
        .filter(CatalogAsset.id == asset_id, CatalogAsset.catalog_id == catalog_id)
        .first()
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录文件不存在")
    if _asset_is_task_input(db, asset_id=asset.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录文件已被任务引用")
    delete_upload(asset.file_path)
    log_operation(
        db,
        action="catalog.asset_deleted",
        target_type="catalog_asset",
        target_id=asset.id,
        actor_id=provider_id,
        detail=asset.file_name,
    )
    db.delete(asset)
    db.commit()


def catalog_has_assets(db: Session, *, catalog_id: int) -> bool:
    return _catalog_has_assets(db, catalog_id=catalog_id)


def _create_catalog_assets(
    db: Session,
    *,
    catalog_id: int,
    files: list[UploadFile],
    provider_id: int,
) -> list[CatalogAsset]:
    assets: list[CatalogAsset] = []
    for upload in files:
        stored = save_catalog_upload(catalog_id=catalog_id, upload=upload)
        asset = CatalogAsset(catalog_id=catalog_id, uploaded_by=provider_id, **stored)
        db.add(asset)
        assets.append(asset)
    db.flush()
    for asset in assets:
        log_operation(
            db,
            action="catalog.asset_uploaded",
            target_type="catalog_asset",
            target_id=asset.id,
            actor_id=provider_id,
            detail=asset.file_name,
        )
    return assets


def _owned_catalog(db: Session, catalog_id: int, provider_id: int) -> Catalog:
    catalog = db.get(Catalog, catalog_id)
    if catalog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录不存在")
    if catalog.provider_id != provider_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return catalog


def _load_catalog(db: Session, catalog_id: int) -> Catalog:
    return (
        db.query(Catalog)
        .options(selectinload(Catalog.assets))
        .filter(Catalog.id == catalog_id)
        .one()
    )


def _ensure_catalog_assets_readable(db: Session, *, catalog_id: int, user: User) -> Catalog:
    catalog = db.get(Catalog, catalog_id)
    if catalog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录不存在")
    if _can_read_catalog_assets(db, catalog=catalog, user=user):
        return catalog
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def _get_readable_catalog_asset(
    db: Session,
    *,
    catalog_id: int,
    asset_id: int,
    user: User,
) -> CatalogAsset:
    _ensure_catalog_assets_readable(db, catalog_id=catalog_id, user=user)
    asset = (
        db.query(CatalogAsset)
        .filter(CatalogAsset.id == asset_id, CatalogAsset.catalog_id == catalog_id)
        .first()
    )
    if asset is not None:
        return asset
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录文件不存在")


def _can_read_catalog_assets(db: Session, *, catalog: Catalog, user: User) -> bool:
    if user.role == UserRole.PROVIDER:
        return catalog.provider_id == user.id
    if user.role != UserRole.AGGREGATOR:
        return False
    demand = (
        db.query(Demand.id)
        .filter(Demand.catalog_id == catalog.id)
        .filter(Demand.requester_id == user.id)
        .filter(Demand.status.in_(READABLE_DEMAND_STATUSES))
        .first()
    )
    return demand is not None


def _asset_is_task_input(db: Session, *, asset_id: int) -> bool:
    task_input = (
        db.query(TaskInputAsset.id)
        .filter(TaskInputAsset.catalog_asset_id == asset_id)
        .first()
    )
    return task_input is not None


def _catalog_has_assets(db: Session, *, catalog_id: int) -> bool:
    asset = db.query(CatalogAsset.id).filter(CatalogAsset.catalog_id == catalog_id).first()
    return asset is not None


def _ensure_uploads_present(files: list[UploadFile]) -> None:
    if files:
        return
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="至少上传一个文件")
