from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.catalog import Catalog, CatalogStatus
from app.services.operation_log_service import log_operation


def create_catalog(db: Session, *, payload, provider_id: int) -> Catalog:
    catalog = Catalog(provider_id=provider_id, status=CatalogStatus.DRAFT, **payload.model_dump())
    db.add(catalog)
    db.flush()
    log_operation(
        db,
        action="catalog.created",
        target_type="catalog",
        target_id=catalog.id,
        actor_id=provider_id,
    )
    db.commit()
    db.refresh(catalog)
    return catalog


def publish_catalog(db: Session, *, catalog_id: int, provider_id: int) -> Catalog:
    catalog = _owned_catalog(db, catalog_id, provider_id)
    if catalog.status != CatalogStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目录状态非法")
    catalog.status = CatalogStatus.PUBLISHED
    log_operation(
        db,
        action="catalog.published",
        target_type="catalog",
        target_id=catalog.id,
        actor_id=provider_id,
    )
    db.commit()
    db.refresh(catalog)
    return catalog


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
    db.refresh(catalog)
    return catalog


def list_my_catalogs(db: Session, *, provider_id: int) -> list[Catalog]:
    return db.query(Catalog).filter(Catalog.provider_id == provider_id).order_by(Catalog.id.desc()).all()


def list_published_catalogs(db: Session) -> list[Catalog]:
    return (
        db.query(Catalog)
        .filter(Catalog.status == CatalogStatus.PUBLISHED)
        .order_by(Catalog.id.desc())
        .all()
    )


def _owned_catalog(db: Session, catalog_id: int, provider_id: int) -> Catalog:
    catalog = db.get(Catalog, catalog_id)
    if catalog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目录不存在")
    if catalog.provider_id != provider_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return catalog
