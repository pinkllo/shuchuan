import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DemandStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DATA_UPLOADED = "data_uploaded"
    PROCESSING = "processing"
    DELIVERED = "delivered"


class Demand(Base):
    __tablename__ = "demands"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey("catalogs.id"), index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(Text)
    delivery_plan: Mapped[str] = mapped_column(String(32))
    status: Mapped[DemandStatus] = mapped_column(
        Enum(DemandStatus),
        default=DemandStatus.PENDING_APPROVAL,
    )
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
