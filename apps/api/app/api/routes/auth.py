from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegistrationCreate,
    RegistrationCreateResponse,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_user, register_application

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegistrationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegistrationCreate,
    db: Session = Depends(get_db),
) -> RegistrationCreateResponse:
    application = register_application(db, payload)
    return RegistrationCreateResponse(id=application.id)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return authenticate_user(db, payload)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
