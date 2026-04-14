from io import BytesIO
from pathlib import Path

from sqlalchemy import text

from app.core.config import settings


def _catalog_form_data() -> dict[str, str]:
    return {
        "name": "课程论坛问答集",
        "data_type": "text",
        "granularity": "主题/帖子/回复",
        "version": "v2026.04",
        "fields_description": "标题、正文、回复内容",
        "scale_description": "约 12000 条",
        "upload_method": "平台上传",
        "sensitivity_level": "internal",
        "description": "教育问答语料",
    }


def _catalog_files(*names: str) -> list[tuple[str, tuple[str, BytesIO, str]]]:
    return [
        ("files", (name, BytesIO(b'{"ok": true}\n'), "application/json"))
        for name in names
    ]


def test_provider_can_create_and_publish_catalog(authenticated_client) -> None:
    client = authenticated_client("provider")

    create_response = client.post(
        "/api/catalogs",
        data=_catalog_form_data(),
        files=_catalog_files("part-1.jsonl", "part-2.jsonl"),
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "draft"
    assert create_response.json()["upload_method"] == "平台上传"
    assert create_response.json()["asset_count"] == 2

    catalog_id = create_response.json()["id"]
    publish_response = client.post(f"/api/catalogs/{catalog_id}/publish")
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"
    assert publish_response.json()["upload_method"] == "平台上传"
    assert publish_response.json()["asset_count"] == 2

    list_response = client.get("/api/catalogs/mine")
    assert list_response.status_code == 200
    assert list_response.json()[0]["status"] == "published"
    assert list_response.json()[0]["upload_method"] == "平台上传"
    assert list_response.json()[0]["asset_count"] == 2


def test_aggregator_only_sees_published_catalogs(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

    provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "科研摘要",
            "granularity": "项目/摘要",
            "version": "v1",
            "fields_description": "项目名、摘要",
            "scale_description": "3200 条",
            "description": "科研摘要数据",
        },
        files=_catalog_files("research.jsonl"),
    )

    response = aggregator_client.get("/api/catalogs")
    assert response.status_code == 200
    assert response.json() == []


def test_provider_can_archive_catalog_and_write_audit_log(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    admin_client = authenticated_client("admin")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "待归档目录",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "200 条",
            "description": "归档审计测试",
        },
        files=_catalog_files("archive.jsonl"),
    )
    catalog_id = create_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    archive_response = provider_client.post(f"/api/catalogs/{catalog_id}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

    logs_response = admin_client.get("/api/admin/logs")
    assert logs_response.status_code == 200
    actions = {item["action"] for item in logs_response.json()}
    assert "catalog.published" in actions
    assert "catalog.archived" in actions


def test_provider_can_manage_catalog_assets(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "目录文件管理目录",
            "description": "目录文件管理测试",
        },
        files=_catalog_files("seed.jsonl"),
    )
    catalog_id = create_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    append_response = provider_client.post(
        f"/api/catalogs/{catalog_id}/assets",
        files=_catalog_files("append-a.jsonl", "append-b.jsonl"),
    )
    assert append_response.status_code == 201
    assert len(append_response.json()) == 2

    provider_assets_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets")
    assert provider_assets_response.status_code == 200
    assert [item["file_name"] for item in provider_assets_response.json()] == [
        "append-b.jsonl",
        "append-a.jsonl",
        "seed.jsonl",
    ]

    aggregator_assets_response = aggregator_client.get(f"/api/catalogs/{catalog_id}/assets")
    assert aggregator_assets_response.status_code == 403

    delete_asset_id = provider_assets_response.json()[0]["id"]
    delete_response = provider_client.delete(
        f"/api/catalogs/{catalog_id}/assets/{delete_asset_id}"
    )
    assert delete_response.status_code == 204

    refreshed_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets")
    assert refreshed_response.status_code == 200
    assert [item["file_name"] for item in refreshed_response.json()] == [
        "append-a.jsonl",
        "seed.jsonl",
    ]


def test_provider_cannot_delete_catalog_asset_referenced_by_task(
    authenticated_client,
    db_session,
) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "任务引用目录",
            "description": "任务引用删除保护测试",
        },
        files=_catalog_files("protected.jsonl"),
    )
    catalog_id = create_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "任务引用需求",
            "purpose": "验证目录文件删除保护",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})

    asset_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets")
    asset_id = asset_response.json()[0]["id"]

    db_session.execute(
        text(
            """
            INSERT INTO processing_tasks
            (demand_id, created_by, task_type, status, progress, config_json, note, created_at, updated_at)
            VALUES
            (:demand_id, :created_by, 'instruction', 'queued', 0, '{}', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "demand_id": demand_id,
            "created_by": demand_response.json()["requester_id"],
        },
    )
    task_id = db_session.execute(text("SELECT MAX(id) FROM processing_tasks")).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO task_input_assets (task_id, catalog_asset_id)
            VALUES (:task_id, :asset_id)
            """
        ),
        {"task_id": task_id, "asset_id": asset_id},
    )
    db_session.commit()

    delete_response = provider_client.delete(f"/api/catalogs/{catalog_id}/assets/{asset_id}")
    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == "目录文件已被任务引用"


def test_provider_can_preview_catalog_asset(authenticated_client) -> None:
    provider_client = authenticated_client("provider")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "目录预览目录",
            "description": "目录预览测试",
        },
        files=[
            (
                "files",
                (
                    "preview.jsonl",
                    BytesIO('{"id": 1, "text": "第一行"}\n{"id": 2, "text": "第二行"}\n'.encode("utf-8")),
                    "application/json",
                ),
            )
        ],
    )
    catalog_id = create_response.json()["id"]
    asset_id = create_response.json()["asset_count"]

    assets_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets")
    asset_id = assets_response.json()[0]["id"]

    preview_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets/{asset_id}/preview")

    assert preview_response.status_code == 200
    assert preview_response.json()["asset_id"] == asset_id
    assert preview_response.json()["file_name"] == "preview.jsonl"
    assert preview_response.json()["file_size"] > 0
    assert preview_response.json()["preview_line_count"] == 2
    assert "第一行" in preview_response.json()["preview_text"]


def test_approved_aggregator_can_preview_catalog_asset(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    owner_client = authenticated_client("aggregator")
    other_client = authenticated_client("aggregator")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "汇聚预览目录",
            "description": "汇聚预览测试",
        },
        files=_catalog_files("approved-preview.jsonl"),
    )
    catalog_id = create_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = owner_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "目录预览需求",
            "purpose": "验证目录文件预览权限",
            "delivery_plan": "2026-05-31",
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})

    assets_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets")
    asset_id = assets_response.json()[0]["id"]

    allowed_response = owner_client.get(f"/api/catalogs/{catalog_id}/assets/{asset_id}/preview")
    denied_response = other_client.get(f"/api/catalogs/{catalog_id}/assets/{asset_id}/preview")

    assert allowed_response.status_code == 200
    assert denied_response.status_code == 403


def test_preview_rejects_non_utf8_catalog_asset(authenticated_client) -> None:
    provider_client = authenticated_client("provider")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "坏编码目录",
            "description": "坏编码预览测试",
        },
        files=_catalog_files("binary-preview.jsonl"),
    )
    catalog_id = create_response.json()["id"]

    assets_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets")
    asset = assets_response.json()[0]
    disk_path = Path(settings.upload_root) / Path(asset["file_path"]).relative_to("uploads")
    disk_path.write_bytes(b"\xff\xfe\x00\x01")

    preview_response = provider_client.get(
        f"/api/catalogs/{catalog_id}/assets/{asset['id']}/preview"
    )

    assert preview_response.status_code == 422
    assert preview_response.json()["detail"] == "目录文件不是可预览的 UTF-8 文本"


def test_pending_aggregator_cannot_preview_catalog_asset(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "待审批预览目录",
            "description": "待审批预览权限测试",
        },
        files=_catalog_files("pending-preview.jsonl"),
    )
    catalog_id = create_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "待审批预览需求",
            "purpose": "验证待审批无权限预览",
            "delivery_plan": "2026-05-31",
        },
    )
    asset_id = provider_client.get(f"/api/catalogs/{catalog_id}/assets").json()[0]["id"]

    preview_response = aggregator_client.get(
        f"/api/catalogs/{catalog_id}/assets/{asset_id}/preview"
    )

    assert preview_response.status_code == 403


def test_provider_can_stream_image_catalog_asset_preview(authenticated_client) -> None:
    provider_client = authenticated_client("provider")

    create_response = provider_client.post(
        "/api/catalogs",
        data={
            **_catalog_form_data(),
            "name": "图片预览目录",
            "description": "图片目录预览测试",
        },
        files=[
            (
                "files",
                (
                    "preview.png",
                    BytesIO(
                        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
                        b"\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c```\x00\x00\x00\x04\x00\x01"
                        b"\x0b\xe7\x02\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
                    ),
                    "image/png",
                ),
            )
        ],
    )
    catalog_id = create_response.json()["id"]
    asset_id = provider_client.get(f"/api/catalogs/{catalog_id}/assets").json()[0]["id"]

    preview_response = provider_client.get(f"/api/catalogs/{catalog_id}/assets/{asset_id}/preview-file")

    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"] == "image/png"
    assert preview_response.content.startswith(b"\x89PNG")
