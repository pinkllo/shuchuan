from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.processor import ProcessorStatus


class ProcessorRegister(BaseModel):
    name: str
    task_type: str
    description: str = ""
    endpoint_url: str


class ProcessorRegisterResponse(BaseModel):
    processor_id: int
    api_token: str
    message: str = "注册成功"


class ProcessorHeartbeat(BaseModel):
    processor_id: int


class ProcessorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    task_type: str
    description: str
    endpoint_url: str
    status: ProcessorStatus
    last_heartbeat_at: datetime
    registered_at: datetime


class TaskProgressReport(BaseModel):
    progress: int = Field(ge=0, le=100)
    message: str = ""


class TaskOutputFile(BaseModel):
    file_path: str
    file_name: str
    sample_count: int = Field(ge=0, default=0)


class TaskCompleteReport(BaseModel):
    output_files: list[TaskOutputFile]
    message: str = ""


class TaskFailReport(BaseModel):
    error: str
    message: str = ""
