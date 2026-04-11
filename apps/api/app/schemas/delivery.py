from datetime import datetime

from pydantic import BaseModel


class DeliveryRead(BaseModel):
    demand_id: int
    demand_title: str
    artifact_file_name: str
    sample_count: int
    delivered_at: datetime
