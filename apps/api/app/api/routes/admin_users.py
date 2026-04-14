from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.schemas.auth import RegistrationReviewRequest, ReviewActionResponse
from app.schemas.user import RegistrationApplicationRead, UserRead
from app.services.auth_service import (
    approve_application,
    disable_user,
    enable_user,
    list_pending_applications,
    list_users,
    reject_application,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get(
    "/registrations",
    response_model=list[RegistrationApplicationRead],
)
def pending_registrations(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[RegistrationApplicationRead]:
    return list_pending_applications(db)


@router.get("/users", response_model=list[UserRead])
def users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[UserRead]:
    return list_users(db)


@router.post(
    "/registrations/{application_id}/approve",
    response_model=ReviewActionResponse,
)
def approve(
    application_id: int,
    payload: RegistrationReviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> ReviewActionResponse:
    approve_application(db, application_id, payload, admin.id)
    return ReviewActionResponse(status="approved")


@router.post(
    "/registrations/{application_id}/reject",
    response_model=ReviewActionResponse,
)
def reject(
    application_id: int,
    payload: RegistrationReviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> ReviewActionResponse:
    reject_application(db, application_id, payload.review_note, admin.id)
    return ReviewActionResponse(status="rejected")


@router.post("/users/{user_id}/disable", response_model=UserRead)
def disable(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserRead:
    user = disable_user(db, user_id, admin.id)
    return UserRead.model_validate(user)


@router.post("/users/{user_id}/enable", response_model=UserRead)
def enable(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserRead:
    user = enable_user(db, user_id, admin.id)
    return UserRead.model_validate(user)
