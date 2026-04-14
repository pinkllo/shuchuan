from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.demand import DemandStatus


class DemandCreate(BaseModel):
    catalog_id: int
    title: str
    purpose: str
    delivery_plan: str


class DemandReview(BaseModel):
    review_note: str


class DemandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_id: int
    requester_id: int
    provider_id: int
    title: str
    purpose: str
    delivery_plan: str
    status: DemandStatus
    approval_note: str | None
    created_at: datetime
