from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.task import TaskStatus


class QuickTaskCreate(BaseModel):
    catalog_id: int
    input_asset_ids: list[int] = Field(min_length=1)
    task_type: str
    config: dict[str, str] = Field(default_factory=dict)


class QuickTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    demand_id: int
    catalog_id: int
    catalog_name: str
    input_asset_ids: list[int]
    task_type: str
    status: TaskStatus
    progress: int
    note: str | None
    processor_id: int | None = None
    processor_name: str | None = None
    created_at: datetime
