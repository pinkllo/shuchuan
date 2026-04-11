from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UploadedAsset(Base):
    __tablename__ = "uploaded_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    demand_id: Mapped[int] = mapped_column(ForeignKey("demands.id"), index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column()
    file_type: Mapped[str] = mapped_column(String(128))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
