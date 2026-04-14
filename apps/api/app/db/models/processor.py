import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessorStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Processor(Base):
    __tablename__ = "processors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    task_type: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    endpoint_url: Mapped[str] = mapped_column(String(512))
    api_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    status: Mapped[ProcessorStatus] = mapped_column(
        Enum(ProcessorStatus),
        default=ProcessorStatus.ONLINE,
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
