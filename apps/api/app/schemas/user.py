from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.db.models.user import RegistrationStatus, UserRole, UserStatus


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    email: EmailStr
    role: UserRole
    status: UserStatus


class RegistrationApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    email: EmailStr
    requested_role: UserRole
    application_note: str
    status: RegistrationStatus
    review_note: str | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
