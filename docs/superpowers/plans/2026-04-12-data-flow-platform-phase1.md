# 数据流转与指令生成系统一期 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 `apps/web` 前端骨架上补齐真实后端、注册审核、角色权限、目录/需求/上传/任务/交付全链路，并将“指令生成”以半接入任务的方式落到系统中。

**Architecture:** 保留现有 Vue 3 单页应用作为前端壳，在 `apps/api` 新建 FastAPI 单体后端，使用 PostgreSQL 持久化业务数据、服务器本地磁盘保存上传文件。前端逐步将本地 Pinia mock store 替换成 API 驱动的 store；后端通过清晰的模型、服务、路由分层来支撑后续“拆书”“病句修改”能力扩展。

**Tech Stack:** Vue 3, TypeScript, Vite, Pinia, Element Plus, Vitest, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest, Docker Compose, Nginx

---

## Execution Notes

- 当前工作区不在 git 仓库内。开始执行本计划前，先在 `d:\数传` 运行 `git init`，否则每个任务的提交步骤都会失败。
- 后端命令在 `d:\数传\apps\api` 执行，前端命令在 `d:\数传\apps\web` 执行。
- 后端单测必须始终使用 60 秒以内的超时，例如 `python -m pytest tests/test_auth_api.py -q`，不要运行无界长任务。

## File Structure

### Backend

- Create: `apps/api/pyproject.toml` — Python 项目依赖、测试配置
- Create: `apps/api/alembic.ini` — Alembic 配置入口
- Create: `apps/api/app/main.py` — FastAPI 应用入口
- Create: `apps/api/app/api/router.py` — 聚合所有 API 路由
- Create: `apps/api/app/api/deps.py` — 数据库会话、当前用户、角色校验依赖
- Create: `apps/api/app/api/routes/health.py` — 健康检查
- Create: `apps/api/app/api/routes/auth.py` — 注册、登录、当前用户
- Create: `apps/api/app/api/routes/admin_users.py` — 管理员审核申请、查看用户
- Create: `apps/api/app/api/routes/admin_logs.py` — 管理员查看操作日志
- Create: `apps/api/app/api/routes/catalogs.py` — 数据目录接口
- Create: `apps/api/app/api/routes/demands.py` — 数据需求接口
- Create: `apps/api/app/api/routes/assets.py` — 原始文件上传与下载
- Create: `apps/api/app/api/routes/tasks.py` — 处理任务和产物接口
- Create: `apps/api/app/api/routes/deliveries.py` — 数据使用者交付列表和下载
- Create: `apps/api/app/core/config.py` — 环境变量配置
- Create: `apps/api/app/core/security.py` — 密码摘要、JWT 签发与解析
- Create: `apps/api/app/db/base.py` — SQLAlchemy Base
- Create: `apps/api/app/db/session.py` — engine、session factory、`get_db`
- Create: `apps/api/app/db/models/user.py` — `User`、`RegistrationApplication`
- Create: `apps/api/app/db/models/catalog.py` — `Catalog`
- Create: `apps/api/app/db/models/demand.py` — `Demand`
- Create: `apps/api/app/db/models/asset.py` — `UploadedAsset`
- Create: `apps/api/app/db/models/task.py` — `ProcessingTask`、`TaskArtifact`
- Create: `apps/api/app/db/models/log.py` — `OperationLog`
- Create: `apps/api/app/schemas/auth.py` — 注册/登录/审核 DTO
- Create: `apps/api/app/schemas/user.py` — 用户 DTO
- Create: `apps/api/app/schemas/catalog.py` — 目录 DTO
- Create: `apps/api/app/schemas/demand.py` — 需求 DTO
- Create: `apps/api/app/schemas/asset.py` — 文件 DTO
- Create: `apps/api/app/schemas/task.py` — 任务 DTO
- Create: `apps/api/app/schemas/delivery.py` — 交付 DTO
- Create: `apps/api/app/services/auth_service.py` — 注册、审核、登录业务
- Create: `apps/api/app/services/catalog_service.py` — 目录业务
- Create: `apps/api/app/services/demand_service.py` — 需求审批与状态推进
- Create: `apps/api/app/services/task_service.py` — 任务创建、状态推进、产物登记
- Create: `apps/api/app/services/file_storage.py` — 本地文件落盘与路径管理
- Create: `apps/api/app/services/operation_log_service.py` — 写操作日志
- Create: `apps/api/app/bootstrap_admin.py` — 初始化管理员账号
- Create: `apps/api/migrations/env.py` — Alembic 环境
- Create: `apps/api/migrations/versions/20260412_0001_auth_and_logs.py`
- Create: `apps/api/migrations/versions/20260412_0002_catalogs.py`
- Create: `apps/api/migrations/versions/20260412_0003_demands_assets.py`
- Create: `apps/api/migrations/versions/20260412_0004_tasks_delivery.py`
- Create: `apps/api/tests/conftest.py` — SQLite 测试数据库、TestClient、鉴权助手
- Create: `apps/api/tests/test_health_api.py`
- Create: `apps/api/tests/test_auth_api.py`
- Create: `apps/api/tests/test_catalog_api.py`
- Create: `apps/api/tests/test_demand_api.py`
- Create: `apps/api/tests/test_task_api.py`
- Create: `apps/api/tests/test_delivery_api.py`
- Create: `apps/api/.env.example`
- Create: `apps/api/Dockerfile`

### Frontend

- Modify: `apps/web/package.json` — 增加 `test` 脚本和 Vitest 依赖
- Create: `apps/web/vitest.config.ts` — 前端测试配置
- Create: `apps/web/src/api/http.ts` — `fetch` 封装、token 注入、错误处理
- Create: `apps/web/src/api/auth.ts`
- Create: `apps/web/src/api/admin.ts`
- Create: `apps/web/src/api/catalogs.ts`
- Create: `apps/web/src/api/demands.ts`
- Create: `apps/web/src/api/assets.ts`
- Create: `apps/web/src/api/tasks.ts`
- Create: `apps/web/src/api/deliveries.ts`
- Create: `apps/web/src/types/auth.ts`
- Create: `apps/web/src/types/catalog.ts`
- Create: `apps/web/src/types/demand.ts`
- Create: `apps/web/src/types/task.ts`
- Create: `apps/web/src/types/delivery.ts`
- Modify: `apps/web/src/stores/session.ts` — 真实 token + 当前用户
- Modify: `apps/web/src/stores/catalogStore.ts` — API 驱动
- Modify: `apps/web/src/stores/demandStore.ts` — API 驱动
- Modify: `apps/web/src/stores/taskStore.ts` — API 驱动
- Modify: `apps/web/src/stores/capabilityStore.ts` — 保留半接入能力元数据
- Modify: `apps/web/src/composables/usePermission.ts` — 增加 `admin` 角色
- Modify: `apps/web/src/router/index.ts` — 登录保护、注册页与管理页
- Modify: `apps/web/src/config/navigation.ts` — 按角色过滤导航
- Modify: `apps/web/src/layout/AppShell.vue` — 展示当前用户、按角色渲染菜单
- Modify: `apps/web/src/pages/LoginPage.vue` — 真实登录表单
- Create: `apps/web/src/pages/RegisterPage.vue`
- Create: `apps/web/src/pages/AdminUserApprovalPage.vue`
- Create: `apps/web/src/pages/AdminUserManagementPage.vue`
- Create: `apps/web/src/pages/AdminAuditLogPage.vue`
- Modify: `apps/web/src/pages/CatalogPage.vue`
- Modify: `apps/web/src/pages/DemandPage.vue`
- Modify: `apps/web/src/pages/ProcessingPage.vue`
- Modify: `apps/web/src/pages/DashboardPage.vue`
- Create: `apps/web/src/pages/DeliveryPage.vue`
- Modify: `apps/web/src/components/CatalogFormDialog.vue`
- Modify: `apps/web/src/components/DemandFormDialog.vue`
- Modify: `apps/web/src/components/ApprovalDialog.vue`
- Modify: `apps/web/src/components/FileUploadDialog.vue`
- Modify: `apps/web/src/components/TaskCreateDialog.vue`
- Modify: `apps/web/src/components/TaskLogDrawer.vue`
- Create: `apps/web/src/stores/__tests__/session.spec.ts`
- Create: `apps/web/src/stores/__tests__/navigation.spec.ts`
- Create: `apps/web/Dockerfile`

### Infra and Docs

- Modify: `.gitignore` — 忽略 `apps/api/.venv`、`apps/api/.pytest_cache`、`uploads/`
- Modify: `README.md` — 本地启动、测试、部署说明
- Create: `docker-compose.yml`
- Create: `nginx/default.conf`

### Task 1: Bootstrap Backend Service And Test Harness

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/api/router.py`
- Create: `apps/api/app/api/routes/health.py`
- Create: `apps/api/app/core/config.py`
- Create: `apps/api/tests/test_health_api.py`
- Modify: `.gitignore`

- [ ] **Step 1: Create the backend manifest, ignore rules, and the failing health test**

```toml
# apps/api/pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "data-platform-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi==0.115.0",
  "uvicorn[standard]==0.30.6",
  "sqlalchemy==2.0.35",
  "alembic==1.13.2",
  "psycopg[binary]==3.2.1",
  "pydantic-settings==2.4.0",
  "python-jose[cryptography]==3.3.0",
  "passlib[argon2]==1.7.4",
  "python-multipart==0.0.9",
  "email-validator==2.2.0"
]

[project.optional-dependencies]
dev = [
  "pytest==8.3.2",
  "httpx==0.27.0"
]

[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
```

```gitignore
# .gitignore
apps/web/node_modules/
apps/web/dist/
apps/api/.venv/
apps/api/.pytest_cache/
apps/api/.coverage
uploads/
```

```python
# apps/api/tests/test_health_api.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Install backend dependencies and verify the test fails for the expected reason**

Run: `python -m pip install -e .[dev]`

Run: `python -m pytest tests/test_health_api.py -q`

Expected: `FAILED tests/test_health_api.py::test_health_returns_ok` with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Write the minimal FastAPI app that satisfies the health test**

```python
# apps/api/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_prefix: str = "/api"
    app_name: str = "data-platform-api"


settings = Settings()
```

```python
# apps/api/app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# apps/api/app/api/router.py
from fastapi import APIRouter

from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(api_router)
```

- [ ] **Step 4: Run the health test again and confirm it passes**

Run: `python -m pytest tests/test_health_api.py -q`

Expected: `1 passed`

- [ ] **Step 5: Commit the backend bootstrap**

```bash
git add .gitignore apps/api/pyproject.toml apps/api/app/main.py apps/api/app/api/router.py apps/api/app/api/routes/health.py apps/api/app/core/config.py apps/api/tests/test_health_api.py
git commit -m "feat: bootstrap fastapi service"
```

### Task 2: Implement Registration Review, Login, And Admin APIs

**Files:**
- Create: `apps/api/alembic.ini`
- Create: `apps/api/app/api/deps.py`
- Create: `apps/api/app/api/routes/auth.py`
- Create: `apps/api/app/api/routes/admin_users.py`
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/app/db/models/user.py`
- Create: `apps/api/app/db/models/log.py`
- Create: `apps/api/app/schemas/auth.py`
- Create: `apps/api/app/schemas/user.py`
- Create: `apps/api/app/core/security.py`
- Create: `apps/api/app/services/auth_service.py`
- Create: `apps/api/app/services/operation_log_service.py`
- Create: `apps/api/migrations/env.py`
- Create: `apps/api/migrations/versions/20260412_0001_auth_and_logs.py`
- Create: `apps/api/tests/conftest.py`
- Create: `apps/api/tests/test_auth_api.py`
- Modify: `apps/api/app/api/router.py`
- Modify: `apps/api/app/core/config.py`

- [ ] **Step 1: Add failing auth and review tests**

```python
# apps/api/tests/conftest.py
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.db.base import Base
from app.main import app


@pytest.fixture()
def db_session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_client(client: TestClient, db_session: Session):
    def factory(role: str) -> TestClient:
        from app.core.security import hash_password
        from app.db.models.user import User, UserRole, UserStatus

        user = User(
            username=f"{role}_user",
            display_name=f"{role} 用户",
            password_hash=hash_password("Passw0rd!"),
            email=f"{role}@example.com",
            role=UserRole(role),
            status=UserStatus.ACTIVE,
        )
        db_session.add(user)
        db_session.commit()

        login_response = client.post(
            "/api/auth/login",
            json={"username": user.username, "password": "Passw0rd!"},
        )
        token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        return client

    return factory
```

```python
# apps/api/tests/test_auth_api.py
def test_registration_requires_admin_review_before_login(client) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "provider_a",
            "display_name": "数据提供者 A",
            "password": "Passw0rd!",
            "email": "provider@example.com",
            "requested_role": "provider",
            "application_note": "申请发布课程论坛问答集"
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
    from app.db.models.user import User, UserRole, UserStatus
    from app.core.security import hash_password

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

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "agg_a",
            "display_name": "汇聚者 A",
            "password": "Passw0rd!",
            "email": "agg@example.com",
            "requested_role": "aggregator",
            "application_note": "负责指令数据整理"
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
```

- [ ] **Step 2: Run the auth tests and confirm they fail before implementation**

Run: `python -m pytest tests/test_auth_api.py -q`

Expected: failures caused by missing `/api/auth/*` routes, missing `User` model, and unresolved `get_db`

- [ ] **Step 3: Implement models, security, auth services, routes, and the first migration**

```python
# apps/api/app/db/models/user.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PROVIDER = "provider"
    AGGREGATOR = "aggregator"
    CONSUMER = "consumer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class RegistrationStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    APPROVED = "approved"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RegistrationApplication(Base):
    __tablename__ = "registration_applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    requested_role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    application_note: Mapped[str] = mapped_column(Text)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus),
        default=RegistrationStatus.PENDING_REVIEW,
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

```python
# apps/api/app/core/security.py
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")
```

```python
# apps/api/app/api/deps.py
from collections.abc import Callable, Iterator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.user import User, UserRole
from app.db.session import SessionLocal

security = HTTPBearer()


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
    user = db.query(User).filter(User.username == payload["sub"]).one()
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
        return current_user

    return dependency
```

```python
# apps/api/app/services/auth_service.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import RegistrationApplication, RegistrationStatus, User, UserStatus


def register_application(db: Session, payload) -> RegistrationApplication:
    application = RegistrationApplication(
        username=payload.username,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        email=payload.email,
        requested_role=payload.requested_role,
        application_note=payload.application_note,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def authenticate_user(db: Session, payload):
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    application = db.query(RegistrationApplication).filter(RegistrationApplication.username == payload.username).one_or_none()
    if not user and application and application.status == RegistrationStatus.PENDING_REVIEW:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号待审核")
    if not user or not verify_password(payload.password, user.password_hash) or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token(user.username)
    return {"access_token": token, "user": user}
```

```python
# apps/api/app/api/routes/auth.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.auth import LoginRequest, RegistrationCreate, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_user, register_application

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegistrationCreate, db: Session = Depends(get_db)) -> dict[str, int]:
    application = register_application(db, payload)
    return {"id": application.id}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return authenticate_user(db, payload)


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
```

```python
# apps/api/app/api/routes/admin_users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import UserRole
from app.schemas.auth import RegistrationReviewRequest
from app.services.auth_service import approve_application, list_pending_applications, reject_application

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/registrations")
def pending_registrations(
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN)),
) -> list[dict]:
    return list_pending_applications(db)


@router.post("/registrations/{application_id}/approve")
def approve(
    application_id: int,
    payload: RegistrationReviewRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
) -> dict[str, str]:
    approve_application(db, application_id, payload, admin.id)
    return {"status": "approved"}


@router.post("/registrations/{application_id}/reject")
def reject(
    application_id: int,
    payload: RegistrationReviewRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
) -> dict[str, str]:
    reject_application(db, application_id, payload.review_note, admin.id)
    return {"status": "rejected"}
```

```python
# apps/api/migrations/versions/20260412_0001_auth_and_logs.py
"""auth and logs"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("admin", "provider", "aggregator", "consumer", name="userrole"), nullable=False),
        sa.Column("status", sa.Enum("active", "disabled", name="userstatus"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
```

- [ ] **Step 4: Apply the migration and rerun the auth tests**

Run: `python -m alembic upgrade head`

Expected: output includes `Running upgrade  -> 20260412_0001`

Run: `python -m pytest tests/test_auth_api.py -q`

Expected: `2 passed`

- [ ] **Step 5: Commit the auth and admin review backend**

```bash
git add apps/api/alembic.ini apps/api/app/api/deps.py apps/api/app/api/routes/auth.py apps/api/app/api/routes/admin_users.py apps/api/app/db/base.py apps/api/app/db/session.py apps/api/app/db/models/user.py apps/api/app/db/models/log.py apps/api/app/schemas/auth.py apps/api/app/schemas/user.py apps/api/app/core/security.py apps/api/app/services/auth_service.py apps/api/app/services/operation_log_service.py apps/api/migrations/env.py apps/api/migrations/versions/20260412_0001_auth_and_logs.py apps/api/tests/conftest.py apps/api/tests/test_auth_api.py apps/api/app/core/config.py apps/api/app/api/router.py
git commit -m "feat: add registration review and login"
```

### Task 3: Replace Mock Login With Real Frontend Auth And Admin Review UI

**Files:**
- Modify: `apps/web/package.json`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/api/http.ts`
- Create: `apps/web/src/api/auth.ts`
- Create: `apps/web/src/api/admin.ts`
- Create: `apps/web/src/types/auth.ts`
- Modify: `apps/web/src/stores/session.ts`
- Modify: `apps/web/src/composables/usePermission.ts`
- Modify: `apps/web/src/router/index.ts`
- Modify: `apps/web/src/config/navigation.ts`
- Modify: `apps/web/src/layout/AppShell.vue`
- Modify: `apps/web/src/pages/LoginPage.vue`
- Create: `apps/web/src/pages/RegisterPage.vue`
- Create: `apps/web/src/pages/AdminUserApprovalPage.vue`
- Create: `apps/web/src/pages/AdminUserManagementPage.vue`
- Create: `apps/web/src/stores/__tests__/session.spec.ts`

- [ ] **Step 1: Add a failing session-store test for token persistence and admin permissions**

```json
// apps/web/package.json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "6.0.1",
    "@vue/test-utils": "2.4.6",
    "jsdom": "25.0.0",
    "typescript": "5.9.2",
    "vite": "7.1.4",
    "vitest": "2.0.5",
    "vue-tsc": "3.0.6"
  }
}
```

```ts
// apps/web/src/stores/__tests__/session.spec.ts
import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useSessionStore } from "@/stores/session";

describe("session store", () => {
  beforeEach(() => {
    sessionStorage.clear();
    setActivePinia(createPinia());
  });

  it("persists the authenticated user and admin role", () => {
    const store = useSessionStore();

    store.setSession({
      accessToken: "token-123",
      user: {
        id: 1,
        username: "admin",
        displayName: "管理员",
        role: "admin",
      },
    });

    expect(store.isAuthenticated).toBe(true);
    expect(store.role).toBe("admin");
    expect(JSON.parse(sessionStorage.getItem("dt-platform-session") ?? "{}").accessToken).toBe("token-123");
  });
});
```

- [ ] **Step 2: Install the new frontend test dependencies and verify the test fails**

Run: `npm install`

Run: `npm run test -- src/stores/__tests__/session.spec.ts`

Expected: failure because `setSession`, `role === "admin"`, and the new persisted shape do not exist yet

- [ ] **Step 3: Implement the real auth client, session store, and admin routes**

```ts
// apps/web/src/api/http.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function http<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(payload.detail ?? "请求失败");
  }

  return response.json() as Promise<T>;
}
```

```ts
// apps/web/src/api/auth.ts
import { http } from "@/api/http";
import type { LoginPayload, RegistrationPayload, SessionPayload } from "@/types/auth";

export function login(payload: LoginPayload) {
  return http<SessionPayload>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitRegistration(payload: RegistrationPayload) {
  return http<{ id: number }>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
```

```ts
// apps/web/src/types/auth.ts
export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegistrationPayload {
  username: string;
  displayName: string;
  password: string;
  email: string;
  requestedRole: "provider" | "aggregator" | "consumer";
  applicationNote: string;
}

export interface SessionPayload {
  accessToken: string;
  user: {
    id: number;
    username: string;
    displayName: string;
    role: "admin" | "provider" | "aggregator" | "consumer";
  };
}
```

```ts
// apps/web/src/stores/session.ts
import { defineStore } from "pinia";

export type UserRole = "admin" | "provider" | "aggregator" | "consumer";

export interface SessionUser {
  id: number;
  username: string;
  displayName: string;
  role: UserRole;
}

interface SessionState {
  accessToken: string | null;
  user: SessionUser | null;
}

const STORAGE_KEY = "dt-platform-session";

function readState(): SessionState {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) as SessionState : { accessToken: null, user: null };
}

export const useSessionStore = defineStore("session", {
  state: (): SessionState => readState(),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
    role: (state) => state.user?.role ?? null,
  },
  actions: {
    setSession(payload: SessionState) {
      this.$state = payload;
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    },
    clearSession() {
      this.$state = { accessToken: null, user: null };
      sessionStorage.removeItem(STORAGE_KEY);
    },
  },
});
```

```ts
// apps/web/src/router/index.ts
{
  path: "/register",
  name: "register",
  component: () => import("@/pages/RegisterPage.vue"),
  meta: { shell: false, title: "提交注册申请" }
},
{
  path: "/admin/approvals",
  name: "admin-approvals",
  component: () => import("@/pages/AdminUserApprovalPage.vue"),
  meta: { auth: true, roles: ["admin"], title: "注册审核" }
},
{
  path: "/admin/users",
  name: "admin-users",
  component: () => import("@/pages/AdminUserManagementPage.vue"),
  meta: { auth: true, roles: ["admin"], title: "用户管理" }
}
```

```vue
<!-- apps/web/src/pages/LoginPage.vue -->
<script setup lang="ts">
import { reactive } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { login } from "@/api/auth";
import { useSessionStore } from "@/stores/session";

const router = useRouter();
const sessionStore = useSessionStore();
const form = reactive({ username: "", password: "" });

async function handleSubmit() {
  const result = await login(form);
  sessionStore.setSession(result);
  ElMessage.success("登录成功");
  router.push({ name: "dashboard" });
}
</script>
```

```vue
<!-- apps/web/src/pages/RegisterPage.vue -->
<script setup lang="ts">
import { reactive } from "vue";
import { ElMessage } from "element-plus";
import { submitRegistration } from "@/api/auth";

const form = reactive({
  username: "",
  displayName: "",
  password: "",
  email: "",
  requestedRole: "provider",
  applicationNote: "",
});

async function handleSubmit() {
  await submitRegistration(form);
  ElMessage.success("注册申请已提交，请等待管理员审核");
}
</script>
```

- [ ] **Step 4: Run the session test and the frontend build**

Run: `npm run test -- src/stores/__tests__/session.spec.ts`

Expected: `1 passed`

Run: `npm run build`

Expected: build succeeds without type errors

- [ ] **Step 5: Commit the real auth frontend**

```bash
git add apps/web/package.json apps/web/vitest.config.ts apps/web/src/api/http.ts apps/web/src/api/auth.ts apps/web/src/api/admin.ts apps/web/src/types/auth.ts apps/web/src/stores/session.ts apps/web/src/composables/usePermission.ts apps/web/src/router/index.ts apps/web/src/config/navigation.ts apps/web/src/layout/AppShell.vue apps/web/src/pages/LoginPage.vue apps/web/src/pages/RegisterPage.vue apps/web/src/pages/AdminUserApprovalPage.vue apps/web/src/pages/AdminUserManagementPage.vue apps/web/src/stores/__tests__/session.spec.ts
git commit -m "feat: wire frontend auth and admin review"
```

### Task 4: Add Catalog APIs And Replace The Catalog Mock Store

**Files:**
- Create: `apps/api/app/db/models/catalog.py`
- Create: `apps/api/app/schemas/catalog.py`
- Create: `apps/api/app/services/catalog_service.py`
- Create: `apps/api/app/api/routes/catalogs.py`
- Create: `apps/api/migrations/versions/20260412_0002_catalogs.py`
- Create: `apps/api/tests/test_catalog_api.py`
- Create: `apps/web/src/api/catalogs.ts`
- Create: `apps/web/src/types/catalog.ts`
- Modify: `apps/web/src/stores/catalogStore.ts`
- Modify: `apps/web/src/pages/CatalogPage.vue`
- Modify: `apps/web/src/components/CatalogFormDialog.vue`
- Modify: `apps/web/src/router/index.ts`

- [ ] **Step 1: Write the failing catalog API tests**

```python
# apps/api/tests/test_catalog_api.py
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
            "description": "教育问答语料"
        },
    )
    assert create_response.status_code == 201

    publish_response = client.post(f"/api/catalogs/{create_response.json()['id']}/publish")
    assert publish_response.status_code == 200

    list_response = client.get("/api/catalogs/mine")
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
            "description": "科研摘要数据"
        },
    )

    response = aggregator_client.get("/api/catalogs")
    assert response.status_code == 200
    assert response.json() == []
```

- [ ] **Step 2: Run the catalog tests and confirm they fail**

Run: `python -m pytest tests/test_catalog_api.py -q`

Expected: failures caused by missing catalog model and `/api/catalogs*` routes

- [ ] **Step 3: Implement the catalog model, service, routes, and migration**

```python
# apps/api/app/db/models/catalog.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CatalogStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Catalog(Base):
    __tablename__ = "catalogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    data_type: Mapped[str] = mapped_column(String(64))
    granularity: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(32))
    fields_description: Mapped[str] = mapped_column(Text)
    scale_description: Mapped[str] = mapped_column(String(128))
    sensitivity_level: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[CatalogStatus] = mapped_column(Enum(CatalogStatus), default=CatalogStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# apps/api/app/api/routes/catalogs.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import UserRole
from app.schemas.catalog import CatalogCreate, CatalogRead
from app.services.catalog_service import create_catalog, list_my_catalogs, list_published_catalogs, publish_catalog

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


@router.get("", response_model=list[CatalogRead])
def list_catalogs(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.AGGREGATOR, UserRole.CONSUMER, UserRole.ADMIN))):
    return list_published_catalogs(db)


@router.get("/mine", response_model=list[CatalogRead])
def mine(db: Session = Depends(get_db), user=Depends(require_roles(UserRole.PROVIDER))):
    return list_my_catalogs(db, user.id)


@router.post("", response_model=CatalogRead, status_code=status.HTTP_201_CREATED)
def create(payload: CatalogCreate, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.PROVIDER))):
    return create_catalog(db, payload, user.id)


@router.post("/{catalog_id}/publish", response_model=CatalogRead)
def publish(catalog_id: int, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.PROVIDER))):
    return publish_catalog(db, catalog_id, user.id)
```

```ts
// apps/web/src/stores/catalogStore.ts
import { defineStore } from "pinia";
import { fetchCatalogs, fetchMyCatalogs, createCatalog, publishCatalog } from "@/api/catalogs";
import type { CatalogCreatePayload, CatalogItem } from "@/types/catalog";

export const useCatalogStore = defineStore("catalog", {
  state: () => ({
    items: [] as CatalogItem[],
    loading: false,
  }),
  actions: {
    async loadPublished() {
      this.loading = true;
      this.items = await fetchCatalogs();
      this.loading = false;
    },
    async loadMine() {
      this.loading = true;
      this.items = await fetchMyCatalogs();
      this.loading = false;
    },
    async submitCatalog(payload: CatalogCreatePayload) {
      const catalog = await createCatalog(payload);
      this.items.unshift(catalog);
      return catalog;
    },
    async publish(id: number) {
      const published = await publishCatalog(id);
      this.items = this.items.map((item) => (item.id === id ? published : item));
    },
  },
});
```

```ts
// apps/web/src/types/catalog.ts
export interface CatalogItem {
  id: number;
  name: string;
  dataType: string;
  granularity: string;
  version: string;
  fieldsDescription: string;
  scaleDescription: string;
  sensitivityLevel: string;
  description: string;
  status: "draft" | "published" | "archived";
}

export interface CatalogCreatePayload {
  name: string;
  dataType: string;
  granularity: string;
  version: string;
  fieldsDescription: string;
  scaleDescription: string;
  sensitivityLevel: string;
  description: string;
}
```

- [ ] **Step 4: Apply the catalog migration and rerun the backend tests**

Run: `python -m alembic upgrade head`

Expected: output includes `Running upgrade 20260412_0001 -> 20260412_0002`

Run: `python -m pytest tests/test_catalog_api.py -q`

Expected: `2 passed`

- [ ] **Step 5: Switch the catalog page to API-backed provider and aggregator views, then build**

```vue
<!-- apps/web/src/pages/CatalogPage.vue -->
<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useCatalogStore } from "@/stores/catalogStore";
import { usePermission } from "@/composables/usePermission";

const store = useCatalogStore();
const { isProvider, isAggregator } = usePermission();

onMounted(() => {
  if (isProvider.value) {
    void store.loadMine();
    return;
  }
  if (isAggregator.value) {
    void store.loadPublished();
  }
});

const emptyText = computed(() => (isProvider.value ? "还没有发布目录" : "当前没有可申请的数据目录"));
</script>
```

Run: `npm run build`

Expected: build succeeds and the catalog page compiles with the new store contract

- [ ] **Step 6: Commit the catalog work**

```bash
git add apps/api/app/db/models/catalog.py apps/api/app/schemas/catalog.py apps/api/app/services/catalog_service.py apps/api/app/api/routes/catalogs.py apps/api/migrations/versions/20260412_0002_catalogs.py apps/api/tests/test_catalog_api.py apps/web/src/api/catalogs.ts apps/web/src/types/catalog.ts apps/web/src/stores/catalogStore.ts apps/web/src/pages/CatalogPage.vue apps/web/src/components/CatalogFormDialog.vue apps/web/src/router/index.ts
git commit -m "feat: add catalog management flow"
```

### Task 5: Implement Demand Approval And Raw File Upload

**Files:**
- Create: `apps/api/app/db/models/demand.py`
- Create: `apps/api/app/db/models/asset.py`
- Create: `apps/api/app/schemas/demand.py`
- Create: `apps/api/app/schemas/asset.py`
- Create: `apps/api/app/services/demand_service.py`
- Create: `apps/api/app/services/file_storage.py`
- Create: `apps/api/app/api/routes/demands.py`
- Create: `apps/api/app/api/routes/assets.py`
- Create: `apps/api/migrations/versions/20260412_0003_demands_assets.py`
- Create: `apps/api/tests/test_demand_api.py`
- Create: `apps/web/src/api/demands.ts`
- Create: `apps/web/src/api/assets.ts`
- Create: `apps/web/src/types/demand.ts`
- Modify: `apps/web/src/stores/demandStore.ts`
- Modify: `apps/web/src/pages/DemandPage.vue`
- Modify: `apps/web/src/components/DemandFormDialog.vue`
- Modify: `apps/web/src/components/ApprovalDialog.vue`
- Modify: `apps/web/src/components/FileUploadDialog.vue`

- [ ] **Step 1: Write the failing demand and upload tests**

```python
# apps/api/tests/test_demand_api.py
from io import BytesIO


def test_aggregator_can_create_demand_for_published_catalog(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    client = authenticated_client("aggregator")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "课程论坛问答集",
            "data_type": "text",
            "granularity": "主题/帖子/回复",
            "version": "v2026.04",
            "fields_description": "标题、正文、回复内容",
            "scale_description": "约 12000 条",
            "sensitivity_level": "internal",
            "description": "教育问答语料"
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    response = client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "教育问答清洗需求",
            "purpose": "构造问答训练样本",
            "delivery_plan": "2026-05-31"
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending_approval"

def test_provider_can_only_upload_after_approval(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "科研摘要",
            "data_type": "text",
            "granularity": "项目/摘要",
            "version": "v1",
            "fields_description": "项目名、摘要",
            "scale_description": "3200 条",
            "sensitivity_level": "internal",
            "description": "科研摘要数据"
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    create_demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "科研摘要清洗需求",
            "purpose": "做指令生成前清洗",
            "delivery_plan": "2026-05-31"
        },
    )
    demand_id = create_demand_response.json()["id"]

    denied_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b'{}'), "application/json")},
    )
    assert denied_response.status_code == 409

    approve_response = provider_client.post(
        f"/api/demands/{demand_id}/approve",
        json={"review_note": "通过"},
    )
    assert approve_response.status_code == 200

    upload_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b'{}'), "application/json")},
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["file_name"] == "sample.jsonl"
```

- [ ] **Step 2: Run the demand tests and confirm they fail**

Run: `python -m pytest tests/test_demand_api.py -q`

Expected: failures caused by missing demand/asset routes and state validation

- [ ] **Step 3: Implement demand status transitions, upload storage, and routes**

```python
# apps/api/app/db/models/demand.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DemandStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DATA_UPLOADED = "data_uploaded"
    PROCESSING = "processing"
    DELIVERED = "delivered"


class Demand(Base):
    __tablename__ = "demands"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey("catalogs.id"), index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(Text)
    delivery_plan: Mapped[str] = mapped_column(String(64))
    status: Mapped[DemandStatus] = mapped_column(Enum(DemandStatus), default=DemandStatus.PENDING_APPROVAL)
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# apps/api/app/services/file_storage.py
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def save_raw_upload(demand_id: int, upload: UploadFile) -> Path:
    target_dir = Path(settings.upload_root) / "raw" / str(demand_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / upload.filename
    data = upload.file.read()
    target_path.write_bytes(data)
    return target_path
```

```python
# apps/api/app/api/routes/demands.py
@router.post("", response_model=DemandRead, status_code=status.HTTP_201_CREATED)
def create(payload: DemandCreate, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.AGGREGATOR))):
    return create_demand(db, payload, user.id)


@router.post("/{demand_id}/approve", response_model=DemandRead)
def approve(demand_id: int, payload: DemandReviewRequest, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.PROVIDER))):
    return approve_demand(db, demand_id, user.id, payload.review_note)
```

```python
# apps/api/app/api/routes/assets.py
@router.post("/api/demands/{demand_id}/assets", response_model=UploadedAssetRead, status_code=status.HTTP_201_CREATED)
def upload_asset(
    demand_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.PROVIDER)),
):
    return upload_raw_asset(db, demand_id, user.id, file)
```

- [ ] **Step 4: Apply the migration and rerun the demand tests**

Run: `python -m alembic upgrade head`

Expected: output includes `Running upgrade 20260412_0002 -> 20260412_0003`

Run: `python -m pytest tests/test_demand_api.py -q`

Expected: `2 passed`

- [ ] **Step 5: Swap the demand page and dialogs to real API calls, then build**

```ts
// apps/web/src/stores/demandStore.ts
import { defineStore } from "pinia";
import { createDemand, fetchDemands, approveDemand } from "@/api/demands";
import { uploadDemandFiles } from "@/api/assets";
import type { DemandCreatePayload, DemandItem } from "@/types/demand";

export const useDemandStore = defineStore("demand", {
  state: () => ({
    items: [] as DemandItem[],
    loading: false,
  }),
  actions: {
    async loadAll() {
      this.loading = true;
      this.items = await fetchDemands();
      this.loading = false;
    },
    async submit(payload: DemandCreatePayload) {
      const demand = await createDemand(payload);
      this.items.unshift(demand);
    },
    async approve(id: number, reviewNote: string) {
      const next = await approveDemand(id, reviewNote);
      this.items = this.items.map((item) => (item.id === id ? next : item));
    },
    async upload(id: number, files: File[]) {
      await uploadDemandFiles(id, files);
      await this.loadAll();
    },
  },
});
```

```ts
// apps/web/src/types/demand.ts
export interface DemandItem {
  id: number;
  catalogId: number;
  title: string;
  purpose: string;
  deliveryPlan: string;
  status: "pending_approval" | "approved" | "rejected" | "data_uploaded" | "processing" | "delivered";
  approvalNote: string | null;
}

export interface DemandCreatePayload {
  catalogId: number;
  title: string;
  purpose: string;
  deliveryPlan: string;
}
```

Run: `npm run build`

Expected: build succeeds with no references to the old in-memory demand simulation

- [ ] **Step 6: Commit the demand and upload flow**

```bash
git add apps/api/app/db/models/demand.py apps/api/app/db/models/asset.py apps/api/app/schemas/demand.py apps/api/app/schemas/asset.py apps/api/app/services/demand_service.py apps/api/app/services/file_storage.py apps/api/app/api/routes/demands.py apps/api/app/api/routes/assets.py apps/api/migrations/versions/20260412_0003_demands_assets.py apps/api/tests/test_demand_api.py apps/web/src/api/demands.ts apps/web/src/api/assets.ts apps/web/src/types/demand.ts apps/web/src/stores/demandStore.ts apps/web/src/pages/DemandPage.vue apps/web/src/components/DemandFormDialog.vue apps/web/src/components/ApprovalDialog.vue apps/web/src/components/FileUploadDialog.vue
git commit -m "feat: add demand approval and upload flow"
```

### Task 6: Implement Processing Tasks And Half-Integrated Instruction Generation

**Files:**
- Create: `apps/api/app/db/models/task.py`
- Create: `apps/api/app/schemas/task.py`
- Create: `apps/api/app/services/task_service.py`
- Create: `apps/api/app/api/routes/tasks.py`
- Create: `apps/api/migrations/versions/20260412_0004_tasks_delivery.py`
- Create: `apps/api/tests/test_task_api.py`
- Create: `apps/web/src/api/tasks.ts`
- Create: `apps/web/src/types/task.ts`
- Modify: `apps/web/src/stores/taskStore.ts`
- Modify: `apps/web/src/pages/ProcessingPage.vue`
- Modify: `apps/web/src/components/TaskCreateDialog.vue`
- Modify: `apps/web/src/components/TaskLogDrawer.vue`
- Modify: `apps/web/src/stores/capabilityStore.ts`

- [ ] **Step 1: Write the failing task API tests**

```python
# apps/api/tests/test_task_api.py
from io import BytesIO


def test_aggregator_can_create_task_after_data_upload(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    client = authenticated_client("aggregator")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "科研摘要",
            "data_type": "text",
            "granularity": "项目/摘要",
            "version": "v1",
            "fields_description": "项目名、摘要",
            "scale_description": "3200 条",
            "sensitivity_level": "internal",
            "description": "科研摘要数据"
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")

    demand_response = client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "摘要转指令需求",
            "purpose": "一期指令生成半接入",
            "delivery_plan": "2026-05-31"
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    upload_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b'{}'), "application/json")},
    )
    asset_id = upload_response.json()["id"]

    response = client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_id,
            "config": {
                "model": "Qwen-2.5-72B",
                "prompt_template": "标准问答模板",
                "batch_size": "32"
            }
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "queued"


def test_task_can_transition_to_completed_with_artifact(authenticated_client) -> None:
    client = authenticated_client("aggregator")
    provider_client = authenticated_client("provider")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "教育问答集",
            "data_type": "text",
            "granularity": "主题/帖子/回复",
            "version": "v1",
            "fields_description": "标题、正文、回复",
            "scale_description": "12000 条",
            "sensitivity_level": "internal",
            "description": "教育问答"
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "教育问答指令需求",
            "purpose": "做半接入指令任务",
            "delivery_plan": "2026-05-31"
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b'{}'), "application/json")},
    )
    task_response = client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_response.json()["id"],
            "config": {
                "model": "Qwen-2.5-72B",
                "prompt_template": "标准问答模板",
                "batch_size": "32"
            }
        },
    )
    task_id = task_response.json()["id"]

    running_response = client.post(f"/api/tasks/{task_id}/status", json={"status": "running", "note": "开始处理"})
    assert running_response.status_code == 200

    completed_response = client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed", "note": "已完成"}
    )
    assert completed_response.status_code == 200

    artifact_response = client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": "instruction-batch-1.jsonl",
            "file_path": "uploads/processed/1/instruction-batch-1.jsonl",
            "sample_count": 1200,
            "note": "一期半接入产物登记"
        },
    )
    assert artifact_response.status_code == 201
```

- [ ] **Step 2: Run the task tests and confirm they fail**

Run: `python -m pytest tests/test_task_api.py -q`

Expected: failures caused by missing task model, status endpoint, and artifact endpoint

- [ ] **Step 3: Implement task models, task routes, and half-integration state transitions**

```python
# apps/api/app/db/models/task.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    demand_id: Mapped[int] = mapped_column(ForeignKey("demands.id"), index=True)
    input_asset_id: Mapped[int] = mapped_column(ForeignKey("uploaded_assets.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    config_json: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# apps/api/app/api/routes/tasks.py
@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.AGGREGATOR))):
    return create_processing_task(db, payload, user.id)


@router.post("/{task_id}/status", response_model=TaskRead)
def update_status(task_id: int, payload: TaskStatusUpdate, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.AGGREGATOR, UserRole.ADMIN))):
    return advance_task_status(db, task_id, payload, user.id)


@router.post("/{task_id}/artifacts", response_model=TaskArtifactRead, status_code=status.HTTP_201_CREATED)
def add_artifact(task_id: int, payload: TaskArtifactCreate, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.AGGREGATOR, UserRole.ADMIN))):
    return create_task_artifact(db, task_id, payload, user.id)
```

```ts
// apps/web/src/stores/taskStore.ts
import { defineStore } from "pinia";
import { createTask, fetchTasks, updateTaskStatus } from "@/api/tasks";
import type { TaskCreatePayload, TaskItem, TaskStatus } from "@/types/task";

export const useTaskStore = defineStore("task", {
  state: () => ({
    items: [] as TaskItem[],
    loading: false,
  }),
  actions: {
    async loadAll() {
      this.loading = true;
      this.items = await fetchTasks();
      this.loading = false;
    },
    async submit(payload: TaskCreatePayload) {
      const task = await createTask(payload);
      this.items.unshift(task);
      return task;
    },
    async updateStatus(id: number, status: TaskStatus, note: string) {
      const next = await updateTaskStatus(id, status, note);
      this.items = this.items.map((item) => (item.id === id ? next : item));
    },
  },
});
```

```ts
// apps/web/src/types/task.ts
export type TaskStatus = "queued" | "running" | "completed" | "failed";

export interface TaskItem {
  id: number;
  demandId: number;
  inputAssetId: number;
  taskType: string;
  status: TaskStatus;
  progress: number;
  config: Record<string, string>;
}

export interface TaskCreatePayload {
  demandId: number;
  inputAssetId: number;
  taskType: string;
  config: Record<string, string>;
}
```

- [ ] **Step 4: Apply the task migration and rerun the backend tests**

Run: `python -m alembic upgrade head`

Expected: output includes `Running upgrade 20260412_0003 -> 20260412_0004`

Run: `python -m pytest tests/test_task_api.py -q`

Expected: `2 passed`

- [ ] **Step 5: Replace the simulated task center with real task APIs and build**

```vue
<!-- apps/web/src/components/TaskCreateDialog.vue -->
<script setup lang="ts">
import { reactive } from "vue";
import { ElMessage } from "element-plus";
import { useTaskStore } from "@/stores/taskStore";

const store = useTaskStore();
const form = reactive({
  demandId: 0,
  inputAssetId: 0,
  taskType: "instruction",
  config: {
    model: "Qwen-2.5-72B",
    promptTemplate: "标准问答模板",
    batchSize: "32",
  },
});

async function handleSubmit() {
  const task = await store.submit(form);
  ElMessage.success(`任务 ${task.id} 已创建`);
}
</script>
```

Run: `npm run build`

Expected: build succeeds and no `setInterval` simulation remains in `taskStore.ts`

- [ ] **Step 6: Commit the task center**

```bash
git add apps/api/app/db/models/task.py apps/api/app/schemas/task.py apps/api/app/services/task_service.py apps/api/app/api/routes/tasks.py apps/api/migrations/versions/20260412_0004_tasks_delivery.py apps/api/tests/test_task_api.py apps/web/src/api/tasks.ts apps/web/src/types/task.ts apps/web/src/stores/taskStore.ts apps/web/src/pages/ProcessingPage.vue apps/web/src/components/TaskCreateDialog.vue apps/web/src/components/TaskLogDrawer.vue apps/web/src/stores/capabilityStore.ts
git commit -m "feat: add processing task center"
```

### Task 7: Add Delivery, Audit Log Pages, And Real Dashboard Data

**Files:**
- Create: `apps/api/app/api/routes/deliveries.py`
- Create: `apps/api/app/api/routes/admin_logs.py`
- Create: `apps/api/app/schemas/delivery.py`
- Create: `apps/api/tests/test_delivery_api.py`
- Create: `apps/web/src/api/deliveries.ts`
- Create: `apps/web/src/pages/DeliveryPage.vue`
- Create: `apps/web/src/pages/AdminAuditLogPage.vue`
- Create: `apps/web/src/stores/__tests__/navigation.spec.ts`
- Modify: `apps/web/src/config/navigation.ts`
- Modify: `apps/web/src/layout/AppShell.vue`
- Modify: `apps/web/src/pages/DashboardPage.vue`
- Modify: `apps/web/src/router/index.ts`

- [ ] **Step 1: Write failing delivery and navigation tests**

```python
# apps/api/tests/test_delivery_api.py
from io import BytesIO


def test_consumer_only_sees_delivered_results(authenticated_client) -> None:
    provider_client = authenticated_client("provider")
    aggregator_client = authenticated_client("aggregator")
    client = authenticated_client("consumer")

    create_catalog_response = provider_client.post(
        "/api/catalogs",
        json={
            "name": "教材问答集",
            "data_type": "text",
            "granularity": "章节/问答",
            "version": "v1",
            "fields_description": "章节、问题、答案",
            "scale_description": "4200 条",
            "sensitivity_level": "internal",
            "description": "教材问答"
        },
    )
    catalog_id = create_catalog_response.json()["id"]
    provider_client.post(f"/api/catalogs/{catalog_id}/publish")
    demand_response = aggregator_client.post(
        "/api/demands",
        json={
            "catalog_id": catalog_id,
            "title": "教材问答交付需求",
            "purpose": "交付给数据使用者",
            "delivery_plan": "2026-05-31"
        },
    )
    demand_id = demand_response.json()["id"]
    provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    asset_response = provider_client.post(
        f"/api/demands/{demand_id}/assets",
        files={"file": ("sample.jsonl", BytesIO(b'{}'), "application/json")},
    )
    task_response = aggregator_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "task_type": "instruction",
            "input_asset_id": asset_response.json()["id"],
            "config": {
                "model": "Qwen-2.5-72B",
                "prompt_template": "标准问答模板",
                "batch_size": "32"
            }
        },
    )
    task_id = task_response.json()["id"]
    aggregator_client.post(f"/api/tasks/{task_id}/status", json={"status": "running", "note": "开始"})
    aggregator_client.post(f"/api/tasks/{task_id}/status", json={"status": "completed", "note": "结束"})
    aggregator_client.post(
        f"/api/tasks/{task_id}/artifacts",
        json={
            "artifact_type": "instruction_jsonl",
            "file_name": "delivery.jsonl",
            "file_path": "uploads/delivery/1/delivery.jsonl",
            "sample_count": 600,
            "note": "交付文件"
        },
    )

    response = client.get("/api/deliveries")
    assert response.status_code == 200
    assert response.json()[0]["demand_id"] == demand_id

    download_response = client.get(f"/api/deliveries/{demand_id}/download")
    assert download_response.status_code == 200


def test_provider_cannot_read_consumer_delivery_list(authenticated_client) -> None:
    client = authenticated_client("provider")
    response = client.get("/api/deliveries")
    assert response.status_code == 403
```

```ts
// apps/web/src/stores/__tests__/navigation.spec.ts
import { describe, expect, it } from "vitest";

import { filterNavItems } from "@/config/navigation";

describe("filterNavItems", () => {
  it("keeps admin pages out of provider navigation", () => {
    const names = filterNavItems("provider").map((item) => item.name);
    expect(names).not.toContain("admin-approvals");
  });
});
```

- [ ] **Step 2: Run the failing delivery and navigation tests**

Run: `python -m pytest tests/test_delivery_api.py -q`

Expected: failures caused by missing `/api/deliveries` and role checks

Run: `npm run test -- src/stores/__tests__/navigation.spec.ts`

Expected: failure because `filterNavItems` does not exist yet

- [ ] **Step 3: Implement delivery listing, admin log listing, and role-filtered navigation**

```python
# apps/api/app/api/routes/deliveries.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.models.user import UserRole
from app.services.task_service import list_deliveries_for_consumer

router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])


@router.get("")
def list_deliveries(db: Session = Depends(get_db), user=Depends(require_roles(UserRole.CONSUMER, UserRole.AGGREGATOR, UserRole.ADMIN))):
    return list_deliveries_for_consumer(db, user)


@router.get("/{demand_id}/download")
def download_delivery(demand_id: int, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.CONSUMER, UserRole.AGGREGATOR, UserRole.ADMIN))):
    return download_delivery_artifact(db, demand_id, user)
```

```python
# apps/api/app/api/routes/admin_logs.py
@router.get("/api/admin/logs")
def list_logs(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.ADMIN))):
    return fetch_recent_logs(db)
```

```ts
// apps/web/src/config/navigation.ts
export function filterNavItems(role: UserRole | null): NavItem[] {
  return navItems.filter((item) => !item.roles || (role ? item.roles.includes(role) : false));
}
```

```vue
<!-- apps/web/src/pages/DeliveryPage.vue -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchDeliveries } from "@/api/deliveries";
import type { DeliveryItem } from "@/types/delivery";

const deliveries = ref<DeliveryItem[]>([]);

onMounted(async () => {
  deliveries.value = await fetchDeliveries();
});

function download(demandId: number) {
  window.open(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/api/deliveries/${demandId}/download`, "_blank");
}
</script>
```

```ts
// apps/web/src/types/delivery.ts
export interface DeliveryItem {
  demandId: number;
  demandTitle: string;
  artifactFileName: string;
  sampleCount: number;
  deliveredAt: string;
}
```

- [ ] **Step 4: Rerun the delivery and navigation tests, then build**

Run: `python -m pytest tests/test_delivery_api.py -q`

Expected: `2 passed`

Run: `npm run test -- src/stores/__tests__/navigation.spec.ts`

Expected: `1 passed`

Run: `npm run build`

Expected: build succeeds with the new delivery and admin log pages

- [ ] **Step 5: Commit the delivery and dashboard work**

```bash
git add apps/api/app/api/routes/deliveries.py apps/api/app/api/routes/admin_logs.py apps/api/app/schemas/delivery.py apps/api/tests/test_delivery_api.py apps/web/src/api/deliveries.ts apps/web/src/pages/DeliveryPage.vue apps/web/src/pages/AdminAuditLogPage.vue apps/web/src/stores/__tests__/navigation.spec.ts apps/web/src/config/navigation.ts apps/web/src/layout/AppShell.vue apps/web/src/pages/DashboardPage.vue apps/web/src/router/index.ts
git commit -m "feat: add delivery and audit views"
```

### Task 8: Add Deployment Assets, Admin Bootstrap, And Final Verification

**Files:**
- Create: `apps/api/app/bootstrap_admin.py`
- Create: `apps/api/.env.example`
- Create: `apps/api/Dockerfile`
- Create: `apps/web/Dockerfile`
- Create: `docker-compose.yml`
- Create: `nginx/default.conf`
- Modify: `README.md`

- [ ] **Step 1: Add admin bootstrap and deployment configuration**

```python
# apps/api/app/bootstrap_admin.py
import argparse

from app.core.security import hash_password
from app.db.models.user import User, UserRole, UserStatus
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    with SessionLocal() as session:
        admin = User(
            username=args.username,
            display_name="管理员",
            password_hash=hash_password(args.password),
            email=args.email,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        session.add(admin)
        session.commit()


if __name__ == "__main__":
    main()
```

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: data_platform
      POSTGRES_USER: data_platform
      POSTGRES_PASSWORD: change_me
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./apps/api
    env_file:
      - ./apps/api/.env.example
    depends_on:
      - postgres
    volumes:
      - ./uploads:/app/uploads

  web:
    build: ./apps/web

  nginx:
    image: nginx:1.27
    depends_on:
      - api
      - web
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro

volumes:
  postgres_data:
```

```nginx
# nginx/default.conf
server {
  listen 80;

  location /api/ {
    proxy_pass http://api:8000/api/;
  }

  location / {
    proxy_pass http://web:80/;
  }
}
```

- [ ] **Step 2: Verify the deployment files are valid**

Run: `docker compose config`

Expected: rendered compose output with `postgres`, `api`, `web`, and `nginx` services

- [ ] **Step 3: Run the full verification suite**

Run: `python -m pytest tests -q`

Expected: all backend tests pass in under 60 seconds

Run: `npm run test`

Expected: all frontend tests pass

Run: `npm run build`

Expected: frontend production build succeeds

- [ ] **Step 4: Update the README with exact startup commands**

```md
# README.md
## 启动后端
1. `cd apps/api`
2. `python -m pip install -e .[dev]`
3. `python -m alembic upgrade head`
4. `python -m app.bootstrap_admin --username admin --password Admin123! --email admin@example.com`
5. `uvicorn app.main:app --reload`

## 启动前端
1. `cd apps/web`
2. `npm install`
3. `npm run dev`
```

- [ ] **Step 5: Commit the deployment and docs**

```bash
git add apps/api/app/bootstrap_admin.py apps/api/.env.example apps/api/Dockerfile apps/web/Dockerfile docker-compose.yml nginx/default.conf README.md
git commit -m "chore: add deployment assets and docs"
```
