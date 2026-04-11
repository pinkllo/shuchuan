from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.asset import AssetRead
from app.services.demand_service import upload_asset

router = APIRouter(prefix="/api/demands", tags=["assets"])


@router.post("/{demand_id}/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def upload_asset_route(
    demand_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> AssetRead:
    return upload_asset(db, demand_id=demand_id, upload=file, provider_id=user.id)
