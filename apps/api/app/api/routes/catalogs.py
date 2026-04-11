from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.catalog import CatalogCreate, CatalogRead
from app.services.catalog_service import (
    archive_catalog,
    create_catalog,
    list_my_catalogs,
    list_published_catalogs,
    publish_catalog,
)

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


@router.post("", response_model=CatalogRead, status_code=status.HTTP_201_CREATED)
def create_catalog_route(
    payload: CatalogCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> CatalogRead:
    return create_catalog(db, payload=payload, provider_id=user.id)


@router.post("/{catalog_id}/publish", response_model=CatalogRead)
def publish_catalog_route(
    catalog_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> CatalogRead:
    return publish_catalog(db, catalog_id=catalog_id, provider_id=user.id)


@router.post("/{catalog_id}/archive", response_model=CatalogRead)
def archive_catalog_route(
    catalog_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> CatalogRead:
    return archive_catalog(db, catalog_id=catalog_id, provider_id=user.id)


@router.get("/mine", response_model=list[CatalogRead])
def list_mine(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> list[CatalogRead]:
    return list_my_catalogs(db, provider_id=user.id)


@router.get("", response_model=list[CatalogRead])
def list_catalogs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGGREGATOR, UserRole.CONSUMER, UserRole.ADMIN)),
) -> list[CatalogRead]:
    return list_published_catalogs(db)
