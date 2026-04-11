import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

USERNAME_LENGTH = 64
DISPLAY_NAME_LENGTH = 128
EMAIL_LENGTH = 255
PASSWORD_HASH_LENGTH = 255


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_type: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_type]


def _db_enum(enum_type: type[enum.Enum], name: str) -> Enum:
    return Enum(
        enum_type,
        name=name,
        values_callable=_enum_values,
    )


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PROVIDER = "provider"
    AGGREGATOR = "aggregator"
    CONSUMER = "consumer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class RegistrationStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(USERNAME_LENGTH), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(DISPLAY_NAME_LENGTH))
    password_hash: Mapped[str] = mapped_column(String(PASSWORD_HASH_LENGTH))
    email: Mapped[str] = mapped_column(String(EMAIL_LENGTH), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(_db_enum(UserRole, "userrole"))
    status: Mapped[UserStatus] = mapped_column(
        _db_enum(UserStatus, "userstatus"),
        default=UserStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class RegistrationApplication(Base):
    __tablename__ = "registration_applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(USERNAME_LENGTH), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(DISPLAY_NAME_LENGTH))
    password_hash: Mapped[str] = mapped_column(String(PASSWORD_HASH_LENGTH))
    email: Mapped[str] = mapped_column(String(EMAIL_LENGTH), unique=True, index=True)
    requested_role: Mapped[UserRole] = mapped_column(_db_enum(UserRole, "userrole"))
    application_note: Mapped[str] = mapped_column(Text)
    status: Mapped[RegistrationStatus] = mapped_column(
        _db_enum(RegistrationStatus, "registrationstatus"),
        default=RegistrationStatus.PENDING_REVIEW,
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
