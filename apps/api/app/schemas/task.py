from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models.task import TaskStatus


class TaskCreate(BaseModel):
    demand_id: int
    task_type: str
    input_asset_ids: list[int] = Field(min_length=1)
    config: dict[str, str]


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    note: str

    @model_validator(mode="after")
    def validate_failed_reason(self) -> "TaskStatusUpdate":
        if self.status == TaskStatus.FAILED and not self.note.strip():
            raise ValueError("失败原因不能为空")
        return self


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    demand_id: int
    input_asset_ids: list[int]
    created_by: int
    processor_id: int | None = None
    processor_name: str | None = None
    task_type: str
    status: TaskStatus
    progress: int
    note: str | None
    created_at: datetime


class TaskArtifactCreate(BaseModel):
    artifact_type: str
    file_name: str
    file_path: str
    sample_count: int
    note: str | None = None


class TaskArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    artifact_type: str
    file_name: str
    file_path: str
    sample_count: int
    note: str | None
    created_at: datetime
