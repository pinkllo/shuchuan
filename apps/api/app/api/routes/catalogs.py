from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.catalog_asset import CatalogAssetPreviewRead, CatalogAssetRead
from app.schemas.catalog import CatalogCreate, CatalogRead
from app.services.catalog_service import (
    add_catalog_assets,
    archive_catalog,
    create_catalog,
    delete_catalog_asset,
    list_catalog_assets_for_user,
    list_my_catalogs,
    list_published_catalogs,
    preview_catalog_asset_file_for_user,
    preview_catalog_asset_for_user,
    publish_catalog,
)

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


@router.post("", response_model=CatalogRead, status_code=status.HTTP_201_CREATED)
def create_catalog_route(
    payload: CatalogCreate = Depends(CatalogCreate.as_form),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> CatalogRead:
    return create_catalog(db, payload=payload, files=files, provider_id=user.id)


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


@router.get(
    "/{catalog_id}/assets",
    response_model=list[CatalogAssetRead],
)
def list_catalog_assets_route(
    catalog_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.AGGREGATOR)),
) -> list[CatalogAssetRead]:
    return list_catalog_assets_for_user(db, catalog_id=catalog_id, user=user)


@router.get(
    "/{catalog_id}/assets/{asset_id}/preview",
    response_model=CatalogAssetPreviewRead,
)
def preview_catalog_asset_route(
    catalog_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.AGGREGATOR)),
) -> CatalogAssetPreviewRead:
    return preview_catalog_asset_for_user(db, catalog_id=catalog_id, asset_id=asset_id, user=user)


@router.get("/{catalog_id}/assets/{asset_id}/preview-file")
def preview_catalog_asset_file_route(
    catalog_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.AGGREGATOR)),
):
    return preview_catalog_asset_file_for_user(
        db,
        catalog_id=catalog_id,
        asset_id=asset_id,
        user=user,
    )


@router.post(
    "/{catalog_id}/assets",
    response_model=list[CatalogAssetRead],
    status_code=status.HTTP_201_CREATED,
)
def add_catalog_assets_route(
    catalog_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> list[CatalogAssetRead]:
    return add_catalog_assets(db, catalog_id=catalog_id, files=files, provider_id=user.id)


@router.delete("/{catalog_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_asset_route(
    catalog_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> None:
    delete_catalog_asset(db, catalog_id=catalog_id, asset_id=asset_id, provider_id=user.id)
