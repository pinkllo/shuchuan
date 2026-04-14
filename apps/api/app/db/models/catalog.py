import enum
from typing import TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.catalog_asset import CatalogAsset


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CatalogStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Catalog(Base):
    __tablename__ = "catalogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    data_type: Mapped[str] = mapped_column(String(32))
    granularity: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(64))
    fields_description: Mapped[str] = mapped_column(Text)
    scale_description: Mapped[str] = mapped_column(String(128))
    upload_method: Mapped[str] = mapped_column(String(64))
    sensitivity_level: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[CatalogStatus] = mapped_column(Enum(CatalogStatus), default=CatalogStatus.DRAFT)
    assets: Mapped[list["CatalogAsset"]] = relationship(
        back_populates="catalog",
        cascade="all, delete-orphan",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    @property
    def asset_count(self) -> int:
        return len(self.assets)
