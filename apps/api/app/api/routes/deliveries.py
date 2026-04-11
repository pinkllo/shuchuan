from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.delivery import DeliveryRead
from app.services.task_service import download_delivery, list_deliveries

router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])


@router.get("", response_model=list[DeliveryRead])
def list_deliveries_route(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.CONSUMER)),
) -> list[DeliveryRead]:
    return list_deliveries(db)


@router.get("/{demand_id}/download")
def download_delivery_route(
    demand_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.CONSUMER)),
):
    return download_delivery(db, demand_id=demand_id, consumer_id=user.id)
