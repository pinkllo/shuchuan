from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.catalog import CatalogStatus


class CatalogCreate(BaseModel):
    name: str
    data_type: str
    granularity: str
    version: str
    fields_description: str
    scale_description: str
    sensitivity_level: str
    description: str


class CatalogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    name: str
    data_type: str
    granularity: str
    version: str
    fields_description: str
    scale_description: str
    sensitivity_level: str
    description: str
    status: CatalogStatus
    created_at: datetime
