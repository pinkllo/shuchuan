from datetime import datetime

from fastapi import Form
from pydantic import BaseModel, ConfigDict

from app.db.models.catalog import CatalogStatus


class CatalogCreate(BaseModel):
    name: str
    data_type: str
    granularity: str
    version: str
    fields_description: str
    scale_description: str
    upload_method: str
    sensitivity_level: str
    description: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        data_type: str = Form(...),
        granularity: str = Form(...),
        version: str = Form(...),
        fields_description: str = Form(...),
        scale_description: str = Form(...),
        upload_method: str = Form(...),
        sensitivity_level: str = Form(...),
        description: str = Form(...),
    ) -> "CatalogCreate":
        return cls(
            name=name,
            data_type=data_type,
            granularity=granularity,
            version=version,
            fields_description=fields_description,
            scale_description=scale_description,
            upload_method=upload_method,
            sensitivity_level=sensitivity_level,
            description=description,
        )


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
    upload_method: str
    sensitivity_level: str
    description: str
    status: CatalogStatus
    asset_count: int
    created_at: datetime
