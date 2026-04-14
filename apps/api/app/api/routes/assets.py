from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.asset import AssetRead
from app.services.demand_service import list_assets_for_user, upload_asset

router = APIRouter(prefix="/api/demands", tags=["assets"])


@router.get("/{demand_id}/assets", response_model=list[AssetRead])
def list_assets_route(
    demand_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.AGGREGATOR)),
) -> list[AssetRead]:
    return list_assets_for_user(db, demand_id=demand_id, user=user)


@router.post("/{demand_id}/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def upload_asset_route(
    demand_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> AssetRead:
    return upload_asset(db, demand_id=demand_id, upload=file, provider_id=user.id)
