def test_provider_can_create_and_publish_catalog(authenticated_client) -> None:
    client = authenticated_client("provider")

    create_response = client.post(
        "/api/catalogs",
        json={
            "name": "课程论坛问答集",
            "data_type": "text",
            "granularity": "主题/帖子/回复",
            "version": "v2026.04",
            "fields_description": "标题、正文、回复内容",
            "scale_description": "约 12000 条",
            "sensitivity_level": "internal",
            "description": "教育问答语料",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "draft"

    catalog_id = create_response.json()["id"]
    publish_response = client.post(f"/api/catalogs/{catalog_id}/publish")
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    list_response = client.get("/api/catalogs/mine")
    assert list_response.status_code == 200
    assert list_response.json()[0]["status"] == "published"


def test_aggregator_only_sees_published_catalogs(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

    provider_client.post(
        "/api/catalogs",
        json={
            "name": "科研摘要",
            "data_type": "text",
            "granularity": "项目/摘要",
            "version": "v1",
            "fields_description": "项目名、摘要",
            "scale_description": "3200 条",
            "sensitivity_level": "internal",
            "description": "科研摘要数据",
        },
    )

    response = aggregator_client.get("/api/catalogs")
    assert response.status_code == 200
    assert response.json() == []


def test_provider_can_archive_catalog_and_write_audit_log(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    admin_client = authenticated_client("admin")

    create_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "待归档目录",
            "data_type": "text",
            "granularity": "主题/帖子",
            "version": "v1",
            "fields_description": "标题、正文",
            "scale_description": "200 条",
            "sensitivity_level": "internal",
            "description": "归档审计测试",
        },
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
