from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import User, UserRole
from app.services.operation_log_service import list_operation_logs

router = APIRouter(prefix="/api/admin", tags=["admin-logs"])


@router.get("/logs")
def list_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[dict[str, object]]:
    logs = list_operation_logs(db)
    return [
        {
            "id": item.id,
            "actor_id": item.actor_id,
            "action": item.action,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "detail": item.detail,
            "created_at": item.created_at.isoformat(),
        }
        for item in logs
    ]
