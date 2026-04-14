from sqlalchemy.orm import Session

from app.db.models.log import OperationLog


def log_operation(
    db: Session,
    action: str,
    target_type: str,
    target_id: int,
    actor_id: int | None = None,
    detail: str | None = None,
) -> OperationLog:
    operation_log = OperationLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(operation_log)
    return operation_log


def list_operation_logs(db: Session) -> list[OperationLog]:
    return (
        db.query(OperationLog)
        .order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
        .all()
    )
