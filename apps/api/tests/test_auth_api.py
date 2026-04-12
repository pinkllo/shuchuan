import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def _api_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _bootstrap_database_url() -> tuple[Path, str]:
    temp_root = _api_dir() / ".test_tmp"
    temp_root.mkdir(exist_ok=True)
    db_path = temp_root / f"bootstrap_{uuid4().hex}.db"
    return db_path, f"sqlite:///{db_path.as_posix()}"


def _create_admin(db_session) -> None:
    from app.core.security import hash_password
    from app.db.models.user import User, UserRole, UserStatus

    admin = User(
        username="admin",
        display_name="管理员",
        password_hash=hash_password("Admin123!"),
        email="admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(admin)
    db_session.commit()


def test_registration_requires_admin_review_before_login(client) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "provider_a",
            "display_name": "数据提供者 A",
            "password": "Passw0rd!",
            "email": "provider@example.com",
            "requested_role": "provider",
            "application_note": "申请发布课程论坛问答集",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"username": "provider_a", "password": "Passw0rd!"},
    )
    assert login_response.status_code == 403
    assert login_response.json()["detail"] == "账号待审核"


def test_admin_can_approve_registration_and_activate_login(client, db_session) -> None:
    _create_admin(db_session)

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "agg_a",
            "display_name": "汇聚者 A",
            "password": "Passw0rd!",
            "email": "agg@example.com",
            "requested_role": "aggregator",
            "application_note": "负责指令数据整理",
        },
    )
    application_id = register_response.json()["id"]

    token_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    token = token_response.json()["access_token"]

    approve_response = client.post(
        f"/api/admin/registrations/{application_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "aggregator", "review_note": "通过"},
    )
    assert approve_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"username": "agg_a", "password": "Passw0rd!"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["role"] == "aggregator"


def test_me_returns_authenticated_user(authenticated_client) -> None:
    client = authenticated_client("consumer")

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "consumer"


def test_rejected_registration_cannot_login(client, db_session) -> None:
    _create_admin(db_session)

    application_id = client.post(
        "/api/auth/register",
        json={
            "username": "consumer_a",
            "display_name": "数据使用者 A",
            "password": "Passw0rd!",
            "email": "consumer@example.com",
            "requested_role": "consumer",
            "application_note": "申请查看交付结果",
        },
    ).json()["id"]
    token = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()["access_token"]

    reject_response = client.post(
        f"/api/admin/registrations/{application_id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "consumer", "review_note": "暂不通过"},
    )
    assert reject_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"username": "consumer_a", "password": "Passw0rd!"},
    )
    assert login_response.status_code == 403
    assert login_response.json()["detail"] == "审核未通过"


def test_admin_can_list_users_and_disable_then_enable_user(client, db_session) -> None:
    from app.core.security import hash_password
    from app.db.models.user import User, UserRole, UserStatus

    _create_admin(db_session)
    provider = User(
        username="provider_live",
        display_name="提供者用户",
        password_hash=hash_password("Passw0rd!"),
        email="provider_live@example.com",
        role=UserRole.PROVIDER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(provider)
    db_session.commit()

    token = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()["access_token"]
    list_response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert any(item["username"] == "provider_live" for item in list_response.json())

    disable_response = client.post(
        f"/api/admin/users/{provider.id}/disable",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"

    disabled_login = client.post(
        "/api/auth/login",
        json={"username": "provider_live", "password": "Passw0rd!"},
    )
    assert disabled_login.status_code == 403
    assert disabled_login.json()["detail"] == "账号已停用"

    enable_response = client.post(
        f"/api/admin/users/{provider.id}/enable",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["status"] == "active"

    enabled_login = client.post(
        "/api/auth/login",
        json={"username": "provider_live", "password": "Passw0rd!"},
    )
    assert enabled_login.status_code == 200


def test_admin_cannot_disable_self(client, db_session) -> None:
    from app.db.models.user import User

    _create_admin(db_session)

    token = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()["access_token"]
    admin = db_session.query(User).filter(User.username == "admin").one()

    disable_response = client.post(
        f"/api/admin/users/{admin.id}/disable",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert disable_response.status_code == 400
    assert disable_response.json()["detail"] == "不能停用当前管理员账号"


def test_bootstrap_admin_creates_active_admin_user() -> None:
    db_path, database_url = _bootstrap_database_url()
    command = [
        sys.executable,
        "-m",
        "app.bootstrap_admin",
        "--username",
        "cli_admin",
        "--password",
        "Admin123!",
        "--email",
        "cli_admin@example.com",
    ]
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url

    try:
        result = subprocess.run(
            command,
            cwd=_api_dir(),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute(
            "select username, role, status, email from users where username = ?",
            ("cli_admin",),
        )
        admin = cursor.fetchone()
        connection.close()
        assert admin == (
            "cli_admin",
            "admin",
            "active",
            "cli_admin@example.com",
        )
    finally:
        if db_path.exists():
            db_path.unlink()
