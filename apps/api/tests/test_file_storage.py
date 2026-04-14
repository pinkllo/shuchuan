from pathlib import Path
from shutil import rmtree

import pytest
from fastapi import HTTPException

from app.services.file_storage import ensure_existing_upload


def test_ensure_existing_upload_rejects_parent_segments() -> None:
    temp_root = Path(".test_tmp") / "file-storage-parent"
    temp_root.mkdir(parents=True, exist_ok=True)
    outside_file = temp_root / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")
    try:
        with pytest.raises(HTTPException) as exc_info:
            ensure_existing_upload("uploads/../outside.txt")
    finally:
        rmtree(temp_root)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "文件路径非法"


def test_ensure_existing_upload_reads_inside_upload_root(monkeypatch) -> None:
    upload_root = Path(".test_tmp") / "file-storage-valid" / "uploads"
    target = upload_root / "catalogs" / "7" / "preview.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("ok", encoding="utf-8")
    monkeypatch.setattr("app.services.file_storage.settings.upload_root", str(upload_root))
    try:
        resolved = ensure_existing_upload("uploads/catalogs/7/preview.jsonl")
    finally:
        rmtree(upload_root.parent)

    assert resolved == target.resolve()
