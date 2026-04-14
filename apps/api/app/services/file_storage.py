from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

UPLOADS_ROOT_NAME = "uploads"
PREVIEW_BYTES_LIMIT = 4096
PREVIEW_TEXT_LIMIT = 2000


def save_demand_upload(*, demand_id: int, upload: UploadFile) -> dict[str, object]:
    return _save_upload(upload=upload, relative_parent=("raw", str(demand_id)))


def save_catalog_upload(*, catalog_id: int, upload: UploadFile) -> dict[str, object]:
    return _save_upload(upload=upload, relative_parent=("catalogs", str(catalog_id)))


def delete_upload(relative_path: str) -> None:
    absolute_path = ensure_existing_upload(relative_path)
    absolute_path.unlink()


def read_text_preview(relative_path: str) -> tuple[str, int, bool]:
    content = _read_preview_bytes(relative_path)
    _ensure_text_content(content)
    return _decode_preview_content(content)


def _save_upload(
    *,
    upload: UploadFile,
    relative_parent: tuple[str, str],
) -> dict[str, object]:
    original_name = Path(upload.filename or "upload.bin").name
    stored_name = f"{uuid4().hex}_{original_name}"
    relative_path = PurePosixPath(UPLOADS_ROOT_NAME, *relative_parent, stored_name)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    return absolute_path


def _read_preview_bytes(relative_path: str) -> bytes:
    absolute_path = ensure_existing_upload(relative_path)
    with absolute_path.open("rb") as file:
        return file.read(PREVIEW_BYTES_LIMIT + 1)


def _ensure_text_content(content: bytes) -> None:
    if b"\x00" in content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="目录文件不是可预览的 UTF-8 文本",
        )


def _decode_preview_content(content: bytes) -> tuple[str, int, bool]:
    truncated = len(content) > PREVIEW_BYTES_LIMIT
    preview_bytes = content[:PREVIEW_BYTES_LIMIT]
    try:
        preview_text = preview_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="目录文件不是可预览的 UTF-8 文本",
        ) from exc
    if len(preview_text) > PREVIEW_TEXT_LIMIT:
        preview_text = preview_text[:PREVIEW_TEXT_LIMIT]
        truncated = True
    preview_line_count = len(preview_text.splitlines())
    return preview_text, preview_line_count, truncated


def _absolute_path(relative_path: str) -> Path:
    normalized = PurePosixPath(relative_path)
    if _is_illegal_upload_path(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件路径非法")
    upload_root = Path(settings.upload_root).resolve()
    absolute_path = upload_root.joinpath(*normalized.parts[1:]).resolve(strict=False)
    if upload_root not in absolute_path.parents and absolute_path != upload_root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件路径非法")
    return absolute_path


def _is_illegal_upload_path(path: PurePosixPath) -> bool:
    if not path.parts or path.parts[0] != UPLOADS_ROOT_NAME:
        return True
    if path.is_absolute():
        return True
    return ".." in path.parts
