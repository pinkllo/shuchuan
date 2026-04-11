from pydantic import BaseModel, EmailStr, Field

from app.db.models.user import UserRole
from app.schemas.user import UserRead

MIN_PASSWORD_LENGTH = 8
MAX_NOTE_LENGTH = 500


class RegistrationCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
    email: EmailStr
    requested_role: UserRole
    application_note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)


class RegistrationCreateResponse(BaseModel):
    id: int


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class RegistrationReviewRequest(BaseModel):
    role: UserRole
    review_note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)


class ReviewActionResponse(BaseModel):
    status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
