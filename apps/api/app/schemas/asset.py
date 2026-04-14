from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    demand_id: int
    uploaded_by: int
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    uploaded_at: datetime
