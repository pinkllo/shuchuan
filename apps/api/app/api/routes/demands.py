from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.demand import DemandCreate, DemandRead, DemandReview
from app.services.demand_service import approve_demand, create_demand, list_demands_for_user

router = APIRouter(prefix="/api/demands", tags=["demands"])


@router.get("", response_model=list[DemandRead])
def list_demands_route(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.AGGREGATOR, UserRole.CONSUMER)),
) -> list[DemandRead]:
    return list_demands_for_user(db, user=user)


@router.post("", response_model=DemandRead, status_code=status.HTTP_201_CREATED)
def create_demand_route(
    payload: DemandCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGGREGATOR)),
) -> DemandRead:
    return create_demand(db, payload=payload, requester_id=user.id)


@router.post("/{demand_id}/approve", response_model=DemandRead)
def approve_demand_route(
    demand_id: int,
    payload: DemandReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PROVIDER)),
) -> DemandRead:
    return approve_demand(
        db,
        demand_id=demand_id,
        review_note=payload.review_note,
        provider_id=user.id,
    )
