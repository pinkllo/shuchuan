from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import (
    RegistrationApplication,
    RegistrationStatus,
    User,
    UserStatus,
    utc_now,
)
from app.schemas.auth import (
    LoginRequest,
    RegistrationCreate,
    RegistrationReviewRequest,
    TokenResponse,
)
from app.schemas.user import RegistrationApplicationRead, UserRead
from app.services.operation_log_service import log_operation

REGISTRATION_TARGET = "registration_application"
USER_TARGET = "user"


def register_application(
    db: Session,
    payload: RegistrationCreate,
) -> RegistrationApplication:
    _ensure_registration_is_unique(db, payload.username, payload.email)
    application = RegistrationApplication(
        username=payload.username,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        email=payload.email,
        requested_role=payload.requested_role,
        application_note=payload.application_note,
    )
    db.add(application)
    db.flush()
    log_operation(
        db,
        action="registration.submitted",
        target_type=REGISTRATION_TARGET,
        target_id=application.id,
    )
    db.commit()
    db.refresh(application)
    return application


def authenticate_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None:
        _raise_application_state_error(db, payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已停用",
        )
    return TokenResponse(
        access_token=create_access_token(user.username),
        user=UserRead.model_validate(user),
    )


def list_pending_applications(db: Session) -> list[RegistrationApplicationRead]:
    applications = (
        db.query(RegistrationApplication)
        .filter(RegistrationApplication.status == RegistrationStatus.PENDING_REVIEW)
        .order_by(RegistrationApplication.created_at.asc())
        .all()
    )
    return [
        RegistrationApplicationRead.model_validate(application)
        for application in applications
    ]


def list_users(db: Session) -> list[UserRead]:
    users = db.query(User).order_by(User.created_at.asc(), User.id.asc()).all()
    return [UserRead.model_validate(user) for user in users]


def approve_application(
    db: Session,
    application_id: int,
    payload: RegistrationReviewRequest,
    admin_id: int,
) -> User:
    application = _get_pending_application(db, application_id)
    _ensure_user_identity_is_available(db, application.username, application.email)
    user = User(
        username=application.username,
        display_name=application.display_name,
        password_hash=application.password_hash,
        email=application.email,
        role=payload.role,
        status=UserStatus.ACTIVE,
    )
    application.status = RegistrationStatus.APPROVED
    application.review_note = payload.review_note
    application.reviewed_by = admin_id
    application.reviewed_at = utc_now()
    db.add(user)
    db.flush()
    log_operation(
        db,
        action="user.activated",
        target_type=USER_TARGET,
        target_id=user.id,
        actor_id=admin_id,
    )
    log_operation(
        db,
        action="registration.approved",
        target_type=REGISTRATION_TARGET,
        target_id=application.id,
        actor_id=admin_id,
        detail=payload.review_note,
    )
    db.commit()
    db.refresh(user)
    return user


def reject_application(
    db: Session,
    application_id: int,
    review_note: str,
    admin_id: int,
) -> RegistrationApplication:
    application = _get_pending_application(db, application_id)
    application.status = RegistrationStatus.REJECTED
    application.review_note = review_note
    application.reviewed_by = admin_id
    application.reviewed_at = utc_now()
    log_operation(
        db,
        action="registration.rejected",
        target_type=REGISTRATION_TARGET,
        target_id=application.id,
        actor_id=admin_id,
        detail=review_note,
    )
    db.commit()
    db.refresh(application)
    return application


def disable_user(db: Session, user_id: int, admin_id: int) -> User:
    return _set_user_status(db, user_id, UserStatus.DISABLED, admin_id, "user.disabled")


def enable_user(db: Session, user_id: int, admin_id: int) -> User:
    return _set_user_status(db, user_id, UserStatus.ACTIVE, admin_id, "user.enabled")


def _ensure_registration_is_unique(db: Session, username: str, email: str) -> None:
    _ensure_user_identity_is_available(db, username, email)
    existing_application = db.query(RegistrationApplication).filter(
        or_(
            RegistrationApplication.username == username,
            RegistrationApplication.email == email,
        ),
    ).one_or_none()
    if existing_application is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已存在",
        )


def _ensure_user_identity_is_available(db: Session, username: str, email: str) -> None:
    existing_user = db.query(User).filter(
        or_(User.username == username, User.email == email),
    ).one_or_none()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已存在",
        )


def _raise_application_state_error(db: Session, username: str) -> None:
    application = db.query(RegistrationApplication).filter(
        RegistrationApplication.username == username,
    ).one_or_none()
    if application is None:
        return
    if application.status == RegistrationStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号待审核",
        )
    if application.status == RegistrationStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="审核未通过",
        )


def _get_pending_application(
    db: Session,
    application_id: int,
) -> RegistrationApplication:
    application = db.get(RegistrationApplication, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="注册申请不存在",
        )
    if application.status != RegistrationStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="注册申请已处理",
        )
    return application


def _set_user_status(
    db: Session,
    user_id: int,
    status_value: UserStatus,
    admin_id: int,
    action: str,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    if user.status != status_value:
        user.status = status_value
        log_operation(
            db,
            action=action,
            target_type=USER_TARGET,
            target_id=user.id,
            actor_id=admin_id,
        )
        db.commit()
        db.refresh(user)
    return user
