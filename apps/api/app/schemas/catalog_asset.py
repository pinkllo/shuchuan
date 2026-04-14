from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CatalogAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_id: int
    uploaded_by: int
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    uploaded_at: datetime


class CatalogAssetPreviewRead(BaseModel):
    asset_id: int
    catalog_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: datetime
    preview_text: str
    preview_line_count: int
    truncated: bool
