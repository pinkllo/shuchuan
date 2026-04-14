from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ACTION_LENGTH = 64
TARGET_TYPE_LENGTH = 64


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(ACTION_LENGTH), index=True)
    target_type: Mapped[str] = mapped_column(String(TARGET_TYPE_LENGTH))
    target_id: Mapped[int] = mapped_column(Integer)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
