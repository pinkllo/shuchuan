from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

UPLOADS_ROOT_NAME = "uploads"


def save_demand_upload(*, demand_id: int, upload: UploadFile) -> dict[str, object]:
    original_name = Path(upload.filename or "upload.bin").name
    stored_name = f"{uuid4().hex}_{original_name}"
    relative_path = PurePosixPath(UPLOADS_ROOT_NAME, "raw", str(demand_id), stored_name)
    absolute_path = _absolute_path(str(relative_path))
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    content = upload.file.read()
    absolute_path.write_bytes(content)
    return {
        "file_name": original_name,
        "file_path": str(relative_path),
        "file_size": len(content),
        "file_type": upload.content_type or "application/octet-stream",
    }


def ensure_existing_upload(relative_path: str) -> Path:
    absolute_path = _absolute_path(relative_path)
    if not absolute_path.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="文件不存在")
    return absolute_path


def _absolute_path(relative_path: str) -> Path:
    normalized = PurePosixPath(relative_path)
    if not normalized.parts or normalized.parts[0] != UPLOADS_ROOT_NAME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件路径非法")
    return Path(settings.upload_root, *normalized.parts[1:])
