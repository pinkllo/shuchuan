import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.processor import Processor


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    demand_id: Mapped[int] = mapped_column(ForeignKey("demands.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    processor_id: Mapped[int | None] = mapped_column(
        ForeignKey("processors.id"),
        nullable=True,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.QUEUED)
    progress: Mapped[int] = mapped_column(default=0)
    config_json: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    input_assets: Mapped[list["TaskInputAsset"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskInputAsset.id",
    )
    processor: Mapped["Processor | None"] = relationship()

    @property
    def input_asset_ids(self) -> list[int]:
        return [item.catalog_asset_id for item in self.input_assets]

    @property
    def processor_name(self) -> str | None:
        if self.processor is None:
            return None
        return self.processor.name


class TaskInputAsset(Base):
    __tablename__ = "task_input_assets"
    __table_args__ = (UniqueConstraint("task_id", "catalog_asset_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("processing_tasks.id"), index=True)
    catalog_asset_id: Mapped[int] = mapped_column(ForeignKey("catalog_assets.id"), index=True)
    task: Mapped["ProcessingTask"] = relationship(back_populates="input_assets")


class TaskArtifact(Base):
    __tablename__ = "task_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("processing_tasks.id"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(64))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))
    sample_count: Mapped[int] = mapped_column()
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
