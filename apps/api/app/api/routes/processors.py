from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.api.processor_auth import authenticate_processor
from app.db.models.processor import Processor
from app.db.models.user import User, UserRole
from app.schemas.processor import (
    ProcessorHeartbeat,
    ProcessorRead,
    ProcessorRegister,
    ProcessorRegisterResponse,
)
from app.services.processor_service import heartbeat, list_processors, register_processor

router = APIRouter(prefix="/api/processors", tags=["processors"])


@router.post(
    "/register",
    response_model=ProcessorRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_route(
    payload: ProcessorRegister,
    db: Session = Depends(get_db),
) -> ProcessorRegisterResponse:
    processor = register_processor(db, payload=payload)
    return ProcessorRegisterResponse(
        processor_id=processor.id,
        api_token=processor.api_token,
    )


@router.post("/heartbeat")
def heartbeat_route(
    payload: ProcessorHeartbeat,
    db: Session = Depends(get_db),
    processor: Processor = Depends(authenticate_processor),
) -> dict[str, str]:
    heartbeat(db, processor_id=payload.processor_id, token=processor.api_token)
    return {"status": "ok"}


@router.get("", response_model=list[ProcessorRead])
def list_route(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGGREGATOR)),
) -> list[Processor]:
    return list_processors(db)
