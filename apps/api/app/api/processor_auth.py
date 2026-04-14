from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.processor import Processor
from app.services.processor_service import get_processor_by_token

processor_security = HTTPBearer()


def authenticate_processor(
    credentials: HTTPAuthorizationCredentials = Depends(processor_security),
    db: Session = Depends(get_db),
) -> Processor:
    return get_processor_by_token(db, credentials.credentials)
