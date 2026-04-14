from datetime import datetime, timedelta, timezone
from secrets import token_hex

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.processor import Processor, ProcessorStatus
from app.schemas.processor import ProcessorRegister

TOKEN_BYTES = 32
TOKEN_PREFIX = "sp_"


def register_processor(db: Session, *, payload: ProcessorRegister) -> Processor:
    processor = _find_by_task_type(db, payload.task_type)
    if processor is None:
        processor = _build_processor(payload)
        db.add(processor)
    else:
        _update_processor(processor, payload)
    db.commit()
    db.refresh(processor)
    return processor


def heartbeat(db: Session, *, processor_id: int, token: str) -> None:
    processor = get_processor_by_token(db, token)
    if processor.id != processor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token 与处理器不匹配",
        )
    _mark_online(processor)
    db.commit()


def list_processors(db: Session) -> list[Processor]:
    processors = db.query(Processor).order_by(Processor.id.asc()).all()
    if _refresh_statuses(processors):
        db.commit()
    return processors


def get_dispatch_processor(db: Session, *, task_type: str) -> Processor | None:
    processor = _find_by_task_type(db, task_type)
    if processor is None:
        return None
    changed = _refresh_statuses([processor])
    if processor.status == ProcessorStatus.OFFLINE:
        if changed:
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="处理器离线",
        )
    if changed:
        db.commit()
    return processor


def get_processor_by_token(db: Session, token: str) -> Processor:
    processor = db.query(Processor).filter(Processor.api_token == token).one_or_none()
    if processor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的处理器 Token",
        )
    return processor


def _build_processor(payload: ProcessorRegister) -> Processor:
    now = _utc_now()
    return Processor(
        name=payload.name,
        task_type=payload.task_type,
        description=payload.description,
        endpoint_url=payload.endpoint_url,
        api_token=f"{TOKEN_PREFIX}{token_hex(TOKEN_BYTES)}",
        status=ProcessorStatus.ONLINE,
        last_heartbeat_at=now,
        registered_at=now,
    )


def _update_processor(processor: Processor, payload: ProcessorRegister) -> None:
    processor.name = payload.name
    processor.description = payload.description
    processor.endpoint_url = payload.endpoint_url
    _mark_online(processor)


def _mark_online(processor: Processor) -> None:
    processor.status = ProcessorStatus.ONLINE
    processor.last_heartbeat_at = _utc_now()


def _refresh_statuses(processors: list[Processor]) -> bool:
    now = _utc_now()
    timeout = timedelta(seconds=settings.processor_heartbeat_timeout)
    changed = False
    for processor in processors:
        if processor.status == ProcessorStatus.OFFLINE:
            continue
        last_heartbeat = _normalize_utc(processor.last_heartbeat_at)
        if now - last_heartbeat > timeout:
            processor.status = ProcessorStatus.OFFLINE
            changed = True
    return changed


def _find_by_task_type(db: Session, task_type: str) -> Processor | None:
    return db.query(Processor).filter(Processor.task_type == task_type).one_or_none()


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
