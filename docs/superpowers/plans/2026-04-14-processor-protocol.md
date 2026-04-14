# Processor Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Processor Protocol that allows external processing services to register with the platform and automatically receive, execute, and report on processing tasks via HTTP REST.

**Architecture:** A new `Processor` model tracks registered external services. The platform dispatches tasks to the processor's `/execute` endpoint when a matching `task_type` is found, and exposes callback endpoints for progress/complete/fail reporting. Token-based authentication secures all inter-service communication. Manual mode is preserved for task types without a registered processor.

**Tech Stack:** Python / FastAPI / SQLAlchemy / Alembic / httpx (async HTTP client) / Vue 3 / TypeScript / Element Plus

**Spec:** `docs/superpowers/specs/2026-04-14-processor-protocol-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `apps/api/app/db/models/processor.py` | Processor SQLAlchemy model |
| `apps/api/app/schemas/processor.py` | Pydantic schemas for processor registration, heartbeat, listing |
| `apps/api/app/services/processor_service.py` | Processor registration, heartbeat, token generation, offline detection |
| `apps/api/app/services/dispatch_service.py` | Task dispatch to processor, handles HTTP call and error fallback |
| `apps/api/app/api/routes/processors.py` | `/api/processors/*` routes (register, heartbeat, list) |
| `apps/api/app/api/routes/task_callbacks.py` | `/api/tasks/{id}/progress\|complete\|fail` callback routes |
| `apps/api/app/api/processor_auth.py` | Processor token authentication dependency |
| `apps/api/migrations/versions/20260414_0007_processors.py` | Alembic migration for processors table + task.processor_id |
| `apps/api/tests/test_processor_api.py` | Tests for processor registration, heartbeat, listing |
| `apps/api/tests/test_task_callbacks.py` | Tests for progress, complete, fail callbacks |
| `apps/api/tests/test_dispatch.py` | Tests for automatic task dispatch logic |
| `apps/web/src/api/processors.ts` | Frontend API client for processors |
| `apps/web/src/types/processor.ts` | TypeScript types for Processor |
| `apps/web/src/pages/AdminProcessorPage.vue` | Admin processor list page |

### Modified Files

| File | Change |
|---|---|
| `apps/api/app/db/base.py` | Add processor model import |
| `apps/api/app/db/models/task.py` | Add `processor_id` nullable FK to ProcessingTask |
| `apps/api/app/schemas/task.py` | Add `processor_id` and `processor_name` to TaskRead |
| `apps/api/app/services/task_service.py` | Integrate dispatch_service in `create_processing_task` |
| `apps/api/app/api/router.py` | Include processors and task_callbacks routers |
| `apps/api/app/core/config.py` | Add `processor_heartbeat_timeout` setting (default 60) |
| `apps/web/src/router/index.ts` | Add admin processor page route |
| `apps/web/src/stores/taskStore.ts` | Add processor info to task display |

---

### Task 1: Processor Model & Migration

**Files:**
- Create: `apps/api/app/db/models/processor.py`
- Modify: `apps/api/app/db/base.py`
- Modify: `apps/api/app/db/models/task.py`
- Create: `apps/api/migrations/versions/20260414_0007_processors.py`

- [ ] **Step 1: Create Processor model**

Create `apps/api/app/db/models/processor.py`:

```python
import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessorStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Processor(Base):
    __tablename__ = "processors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    task_type: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    endpoint_url: Mapped[str] = mapped_column(String(512))
    api_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    status: Mapped[ProcessorStatus] = mapped_column(
        Enum(ProcessorStatus), default=ProcessorStatus.ONLINE
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
```

- [ ] **Step 2: Add processor_id to ProcessingTask**

In `apps/api/app/db/models/task.py`, add after `created_by` field:

```python
processor_id: Mapped[int | None] = mapped_column(ForeignKey("processors.id"), nullable=True)
```

- [ ] **Step 3: Register processor model in base.py**

In `apps/api/app/db/base.py`, update import line to include `processor`:

```python
from app.db.models import asset, catalog, catalog_asset, demand, log, processor, task, user  # noqa: E402,F401
```

- [ ] **Step 4: Create Alembic migration**

Create `apps/api/migrations/versions/20260414_0007_processors.py`:

```python
"""Add processors table and task.processor_id

Revision ID: 0007
Revises: 20260412_0006
"""
from alembic import op
import sqlalchemy as sa

revision = "20260414_0007"
down_revision = "20260412_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("endpoint_url", sa.String(512), nullable=False),
        sa.Column("api_token", sa.String(128), nullable=False),
        sa.Column("status", sa.Enum("online", "offline", name="processorstatus"), nullable=False, server_default="online"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_type"),
        sa.UniqueConstraint("api_token"),
    )
    op.create_index("ix_processors_task_type", "processors", ["task_type"])
    op.create_index("ix_processors_api_token", "processors", ["api_token"])
    op.add_column("processing_tasks", sa.Column("processor_id", sa.Integer(), sa.ForeignKey("processors.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("processing_tasks", "processor_id")
    op.drop_index("ix_processors_api_token", "processors")
    op.drop_index("ix_processors_task_type", "processors")
    op.drop_table("processors")
    op.execute("DROP TYPE IF EXISTS processorstatus")
```

- [ ] **Step 5: Verify migration applies cleanly**

Run: `python -m pytest apps/api/tests/test_health_api.py -v`
Expected: PASS (tests use in-memory DB that picks up new models via `Base.metadata.create_all`)

- [ ] **Step 6: Commit**

```
git add apps/api/app/db/models/processor.py apps/api/app/db/base.py apps/api/app/db/models/task.py apps/api/migrations/versions/20260414_0007_processors.py
git commit -m "feat: add Processor model and migration"
```

---

### Task 2: Processor Schemas & Config

**Files:**
- Create: `apps/api/app/schemas/processor.py`
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/app/schemas/task.py`

- [ ] **Step 1: Create processor schemas**

Create `apps/api/app/schemas/processor.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProcessorRegister(BaseModel):
    name: str
    task_type: str
    description: str = ""
    endpoint_url: str


class ProcessorRegisterResponse(BaseModel):
    processor_id: int
    api_token: str
    message: str = "注册成功"


class ProcessorHeartbeat(BaseModel):
    processor_id: int


class ProcessorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    task_type: str
    description: str
    endpoint_url: str
    status: str
    last_heartbeat_at: datetime
    registered_at: datetime
```

- [ ] **Step 2: Add heartbeat timeout to config**

In `apps/api/app/core/config.py`, add to `Settings` class:

```python
processor_heartbeat_timeout: int = 60
```

- [ ] **Step 3: Add processor_id to TaskRead**

In `apps/api/app/schemas/task.py`, add to `TaskRead` class after `created_by`:

```python
processor_id: int | None = None
```

- [ ] **Step 4: Commit**

```
git add apps/api/app/schemas/processor.py apps/api/app/core/config.py apps/api/app/schemas/task.py
git commit -m "feat: add Processor schemas and config"
```

---

### Task 3: Processor Service (Registration & Heartbeat)

**Files:**
- Create: `apps/api/app/services/processor_service.py`
- Create: `apps/api/tests/test_processor_api.py`

- [ ] **Step 1: Write failing tests for processor registration**

Create `apps/api/tests/test_processor_api.py`:

```python
def test_register_processor(client):
    resp = client.post("/api/processors/register", json={
        "name": "拆书服务",
        "task_type": "book_split",
        "description": "将书籍拆分为章节段落",
        "endpoint_url": "http://localhost:9001",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["processor_id"] > 0
    assert data["api_token"].startswith("sp_")
    assert data["message"] == "注册成功"


def test_register_processor_idempotent(client):
    payload = {
        "name": "拆书服务",
        "task_type": "book_split",
        "description": "v1",
        "endpoint_url": "http://localhost:9001",
    }
    resp1 = client.post("/api/processors/register", json=payload)
    token1 = resp1.json()["api_token"]
    payload["description"] = "v2"
    payload["endpoint_url"] = "http://localhost:9002"
    resp2 = client.post("/api/processors/register", json=payload)
    assert resp2.json()["api_token"] == token1
    assert resp2.json()["processor_id"] == resp1.json()["processor_id"]


def test_heartbeat_success(client):
    reg = client.post("/api/processors/register", json={
        "name": "test", "task_type": "test_type",
        "description": "", "endpoint_url": "http://localhost:9999",
    })
    data = reg.json()
    resp = client.post(
        "/api/processors/heartbeat",
        json={"processor_id": data["processor_id"]},
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_heartbeat_wrong_token(client):
    reg = client.post("/api/processors/register", json={
        "name": "test", "task_type": "ht",
        "description": "", "endpoint_url": "http://localhost:9999",
    })
    resp = client.post(
        "/api/processors/heartbeat",
        json={"processor_id": reg.json()["processor_id"]},
        headers={"Authorization": "Bearer sp_wrong_token"},
    )
    assert resp.status_code == 403


def test_list_processors_admin_only(authenticated_client):
    admin = authenticated_client("admin")
    agg = authenticated_client("aggregator")
    resp_admin = admin.get("/api/processors")
    assert resp_admin.status_code == 200
    resp_agg = agg.get("/api/processors")
    assert resp_agg.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest apps/api/tests/test_processor_api.py -v`
Expected: FAIL (routes not yet created)

- [ ] **Step 3: Create processor_service.py**

Create `apps/api/app/services/processor_service.py`:

```python
from datetime import datetime, timezone
from secrets import token_hex

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.processor import Processor, ProcessorStatus

TOKEN_PREFIX = "sp_"


def register_processor(db: Session, *, payload) -> Processor:
    existing = db.query(Processor).filter(Processor.task_type == payload.task_type).one_or_none()
    if existing is not None:
        existing.name = payload.name
        existing.description = payload.description
        existing.endpoint_url = payload.endpoint_url
        existing.status = ProcessorStatus.ONLINE
        existing.last_heartbeat_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    processor = Processor(
        name=payload.name,
        task_type=payload.task_type,
        description=payload.description,
        endpoint_url=payload.endpoint_url,
        api_token=f"{TOKEN_PREFIX}{token_hex(32)}",
        status=ProcessorStatus.ONLINE,
        last_heartbeat_at=datetime.now(timezone.utc),
        registered_at=datetime.now(timezone.utc),
    )
    db.add(processor)
    db.commit()
    db.refresh(processor)
    return processor


def heartbeat(db: Session, *, processor_id: int, token: str) -> None:
    processor = _get_processor_by_token(db, token)
    if processor.id != processor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token 与处理器不匹配")
    processor.last_heartbeat_at = datetime.now(timezone.utc)
    processor.status = ProcessorStatus.ONLINE
    db.commit()


def list_processors(db: Session) -> list[Processor]:
    return db.query(Processor).order_by(Processor.id).all()


def get_online_processor_by_task_type(db: Session, task_type: str) -> Processor | None:
    return (
        db.query(Processor)
        .filter(Processor.task_type == task_type, Processor.status == ProcessorStatus.ONLINE)
        .one_or_none()
    )


def _get_processor_by_token(db: Session, token: str) -> Processor:
    processor = db.query(Processor).filter(Processor.api_token == token).one_or_none()
    if processor is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效的处理器 Token")
    return processor
```

- [ ] **Step 4: Create processor_auth.py dependency**

Create `apps/api/app/api/processor_auth.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.processor import Processor

processor_security = HTTPBearer()


def get_processor_by_token(
    credentials: HTTPAuthorizationCredentials = Depends(processor_security),
    db: Session = Depends(get_db),
) -> Processor:
    token = credentials.credentials
    processor = db.query(Processor).filter(Processor.api_token == token).one_or_none()
    if processor is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效的处理器 Token")
    return processor
```

- [ ] **Step 5: Create processor routes**

Create `apps/api/app/api/routes/processors.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.api.processor_auth import get_processor_by_token
from app.db.models.processor import Processor
from app.db.models.user import User, UserRole
from app.schemas.processor import (
    ProcessorHeartbeat,
    ProcessorRead,
    ProcessorRegister,
    ProcessorRegisterResponse,
)
from app.services.processor_service import heartbeat, list_processors, register_processor

router = APIRouter(prefix="/api/processors", tags=["processors"])


@router.post("/register", response_model=ProcessorRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_route(payload: ProcessorRegister, db: Session = Depends(get_db)) -> ProcessorRegisterResponse:
    processor = register_processor(db, payload=payload)
    return ProcessorRegisterResponse(processor_id=processor.id, api_token=processor.api_token)


@router.post("/heartbeat")
def heartbeat_route(
    payload: ProcessorHeartbeat,
    db: Session = Depends(get_db),
    processor: Processor = Depends(get_processor_by_token),
) -> dict[str, str]:
    heartbeat(db, processor_id=payload.processor_id, token=processor.api_token)
    return {"status": "ok"}


@router.get("", response_model=list[ProcessorRead])
def list_route(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[ProcessorRead]:
    return list_processors(db)
```

- [ ] **Step 6: Register routes in router.py**

In `apps/api/app/api/router.py`, add import and include:

```python
from app.api.routes.processors import router as processors_router
# ... existing includes ...
api_router.include_router(processors_router)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest apps/api/tests/test_processor_api.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```
git add apps/api/app/services/processor_service.py apps/api/app/api/processor_auth.py apps/api/app/api/routes/processors.py apps/api/app/api/router.py apps/api/tests/test_processor_api.py
git commit -m "feat: implement processor registration, heartbeat, and listing"
```

---

### Task 4: Task Callback Endpoints (Progress / Complete / Fail)

**Files:**
- Create: `apps/api/app/api/routes/task_callbacks.py`
- Create: `apps/api/tests/test_task_callbacks.py`

- [ ] **Step 1: Write failing tests for task callbacks**

Create `apps/api/tests/test_task_callbacks.py`:

```python
import pytest
from tests.conftest import *  # noqa: F403


@pytest.fixture()
def processor_and_task(client, authenticated_client, db_session):
    """Set up a processor, a provider catalog, an aggregator demand, and a task."""
    from app.db.models.catalog import Catalog, CatalogStatus
    from app.db.models.catalog_asset import CatalogAsset
    from app.db.models.demand import Demand, DemandStatus
    from app.db.models.task import ProcessingTask, TaskInputAsset, TaskStatus

    # Register processor
    reg = client.post("/api/processors/register", json={
        "name": "test-proc", "task_type": "instruction",
        "description": "test", "endpoint_url": "http://localhost:9999",
    })
    proc_data = reg.json()

    # Create provider user and catalog via DB
    provider = authenticated_client("provider")
    aggregator = authenticated_client("aggregator")
    from app.db.models.user import User
    provider_user = db_session.query(User).filter(User.username.like("provider%")).first()
    agg_user = db_session.query(User).filter(User.username.like("aggregator%")).first()

    catalog = Catalog(
        provider_id=provider_user.id, name="test", data_type="text",
        granularity="doc", version="1.0", fields_description="f",
        scale_description="s", upload_method="batch", sensitivity_level="low",
        description="d", status=CatalogStatus.PUBLISHED,
    )
    db_session.add(catalog)
    db_session.flush()
    asset = CatalogAsset(
        catalog_id=catalog.id, uploaded_by=provider_user.id,
        file_name="test.txt", file_path="uploads/catalogs/1/test.txt",
        file_size=100, file_type="text/plain",
    )
    db_session.add(asset)
    db_session.flush()
    demand = Demand(
        catalog_id=catalog.id, requester_id=agg_user.id,
        provider_id=provider_user.id, title="test demand",
        purpose="test", delivery_plan="online",
        status=DemandStatus.DATA_UPLOADED,
    )
    db_session.add(demand)
    db_session.flush()
    task = ProcessingTask(
        demand_id=demand.id, created_by=agg_user.id,
        task_type="instruction", status=TaskStatus.RUNNING,
        config_json={}, processor_id=proc_data["processor_id"],
    )
    db_session.add(task)
    db_session.flush()
    db_session.add(TaskInputAsset(task_id=task.id, catalog_asset_id=asset.id))
    db_session.commit()

    return {
        "api_token": proc_data["api_token"],
        "task_id": task.id,
        "demand_id": demand.id,
    }


def test_progress(client, processor_and_task):
    data = processor_and_task
    resp = client.post(
        f"/api/tasks/{data['task_id']}/progress",
        json={"progress": 50, "message": "half done"},
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["progress"] == 50


def test_complete(client, processor_and_task):
    import os
    from app.core.config import settings
    # Create output file
    out_dir = os.path.join(settings.upload_root, "delivery", f"task_{processor_and_task['task_id']}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "result.json")
    with open(out_path, "w") as f:
        f.write("{}")
    rel_path = f"uploads/delivery/task_{processor_and_task['task_id']}/result.json"

    data = processor_and_task
    resp = client.post(
        f"/api/tasks/{data['task_id']}/complete",
        json={
            "output_files": [{"file_path": rel_path, "file_name": "result.json", "sample_count": 100}],
            "message": "done",
        },
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_fail(client, processor_and_task):
    data = processor_and_task
    resp = client.post(
        f"/api/tasks/{data['task_id']}/fail",
        json={"error": "format error", "message": "unsupported file"},
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"


def test_callback_wrong_token(client, processor_and_task):
    data = processor_and_task
    resp = client.post(
        f"/api/tasks/{data['task_id']}/progress",
        json={"progress": 10, "message": "test"},
        headers={"Authorization": "Bearer sp_wrong"},
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest apps/api/tests/test_task_callbacks.py -v`
Expected: FAIL

- [ ] **Step 3: Create callback schemas**

Add to `apps/api/app/schemas/processor.py`:

```python
class TaskProgressReport(BaseModel):
    progress: int
    message: str = ""


class TaskCompleteReport(BaseModel):
    output_files: list[dict]
    message: str = ""


class TaskFailReport(BaseModel):
    error: str
    message: str = ""
```

- [ ] **Step 4: Create task_callbacks.py routes**

Create `apps/api/app/api/routes/task_callbacks.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.processor_auth import get_processor_by_token
from app.db.models.demand import Demand, DemandStatus
from app.db.models.processor import Processor
from app.db.models.task import ProcessingTask, TaskArtifact, TaskStatus
from app.schemas.processor import TaskCompleteReport, TaskFailReport, TaskProgressReport
from app.services.file_storage import ensure_existing_upload
from app.services.operation_log_service import log_operation

router = APIRouter(prefix="/api/tasks", tags=["task-callbacks"])


def _get_task_for_processor(db: Session, task_id: int, processor: Processor) -> ProcessingTask:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.processor_id != processor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此任务")
    return task


@router.post("/{task_id}/progress")
def report_progress(
    task_id: int,
    payload: TaskProgressReport,
    db: Session = Depends(get_db),
    processor: Processor = Depends(get_processor_by_token),
) -> dict:
    task = _get_task_for_processor(db, task_id, processor)
    task.progress = payload.progress
    if payload.message:
        task.note = payload.message
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "progress": task.progress, "status": task.status.value}


@router.post("/{task_id}/complete")
def report_complete(
    task_id: int,
    payload: TaskCompleteReport,
    db: Session = Depends(get_db),
    processor: Processor = Depends(get_processor_by_token),
) -> dict:
    task = _get_task_for_processor(db, task_id, processor)
    task.status = TaskStatus.COMPLETED
    task.progress = 100
    if payload.message:
        task.note = payload.message
    for file_info in payload.output_files:
        ensure_existing_upload(file_info["file_path"])
        artifact = TaskArtifact(
            task_id=task.id,
            artifact_type="processor_output",
            file_name=file_info["file_name"],
            file_path=file_info["file_path"],
            sample_count=file_info.get("sample_count", 0),
            note=payload.message,
        )
        db.add(artifact)
        if file_info["file_path"].startswith("uploads/delivery/"):
            demand = db.get(Demand, task.demand_id)
            if demand is not None:
                demand.status = DemandStatus.DELIVERED
    db.flush()
    log_operation(
        db, action="task.completed_by_processor",
        target_type="processing_task", target_id=task.id,
        detail=payload.message,
    )
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "status": task.status.value, "progress": task.progress}


@router.post("/{task_id}/fail")
def report_fail(
    task_id: int,
    payload: TaskFailReport,
    db: Session = Depends(get_db),
    processor: Processor = Depends(get_processor_by_token),
) -> dict:
    task = _get_task_for_processor(db, task_id, processor)
    task.status = TaskStatus.FAILED
    task.note = f"{payload.error}: {payload.message}" if payload.message else payload.error
    db.flush()
    log_operation(
        db, action="task.failed_by_processor",
        target_type="processing_task", target_id=task.id,
        detail=task.note,
    )
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "status": task.status.value}
```

- [ ] **Step 5: Register callback routes in router.py**

In `apps/api/app/api/router.py`, add:

```python
from app.api.routes.task_callbacks import router as task_callbacks_router
api_router.include_router(task_callbacks_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest apps/api/tests/test_task_callbacks.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```
git add apps/api/app/schemas/processor.py apps/api/app/api/routes/task_callbacks.py apps/api/app/api/router.py apps/api/tests/test_task_callbacks.py
git commit -m "feat: implement task callback endpoints (progress/complete/fail)"
```

---

### Task 5: Dispatch Service & Task Creation Integration

**Files:**
- Create: `apps/api/app/services/dispatch_service.py`
- Modify: `apps/api/app/services/task_service.py`
- Create: `apps/api/tests/test_dispatch.py`

- [ ] **Step 1: Write failing dispatch test**

Create `apps/api/tests/test_dispatch.py`:

```python
from unittest.mock import patch, MagicMock


def test_task_auto_dispatched_to_processor(client, authenticated_client, db_session):
    """When a processor is registered for task_type, creating a task should auto-dispatch."""
    from app.db.models.catalog import Catalog, CatalogStatus
    from app.db.models.catalog_asset import CatalogAsset
    from app.db.models.demand import Demand, DemandStatus
    from app.db.models.user import User

    # Register processor
    client.post("/api/processors/register", json={
        "name": "auto-proc", "task_type": "instruction",
        "description": "auto", "endpoint_url": "http://localhost:9999",
    })

    # Set up data
    provider = authenticated_client("provider")
    aggregator = authenticated_client("aggregator")
    provider_user = db_session.query(User).filter(User.username.like("provider%")).first()
    agg_user = db_session.query(User).filter(User.username.like("aggregator%")).first()

    catalog = Catalog(
        provider_id=provider_user.id, name="test", data_type="text",
        granularity="doc", version="1.0", fields_description="f",
        scale_description="s", upload_method="batch", sensitivity_level="low",
        description="d", status=CatalogStatus.PUBLISHED,
    )
    db_session.add(catalog)
    db_session.flush()
    asset = CatalogAsset(
        catalog_id=catalog.id, uploaded_by=provider_user.id,
        file_name="test.txt", file_path="uploads/catalogs/1/test.txt",
        file_size=100, file_type="text/plain",
    )
    db_session.add(asset)
    db_session.flush()
    demand = Demand(
        catalog_id=catalog.id, requester_id=agg_user.id,
        provider_id=provider_user.id, title="test",
        purpose="test", delivery_plan="online",
        status=DemandStatus.DATA_UPLOADED,
    )
    db_session.add(demand)
    db_session.commit()

    # Mock httpx call to processor
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.json.return_value = {"accepted": True}
    with patch("app.services.dispatch_service.httpx") as mock_httpx:
        mock_httpx.post.return_value = mock_response
        resp = aggregator.post("/api/tasks", json={
            "demand_id": demand.id,
            "input_asset_ids": [asset.id],
            "task_type": "instruction",
            "config": {},
        })

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "running"
    assert data["processor_id"] is not None


def test_task_manual_mode_without_processor(client, authenticated_client, db_session):
    """Without a matching processor, task stays in queued manual mode."""
    from app.db.models.catalog import Catalog, CatalogStatus
    from app.db.models.catalog_asset import CatalogAsset
    from app.db.models.demand import Demand, DemandStatus
    from app.db.models.user import User

    provider = authenticated_client("provider")
    aggregator = authenticated_client("aggregator")
    provider_user = db_session.query(User).filter(User.username.like("provider%")).first()
    agg_user = db_session.query(User).filter(User.username.like("aggregator%")).first()

    catalog = Catalog(
        provider_id=provider_user.id, name="test", data_type="text",
        granularity="doc", version="1.0", fields_description="f",
        scale_description="s", upload_method="batch", sensitivity_level="low",
        description="d", status=CatalogStatus.PUBLISHED,
    )
    db_session.add(catalog)
    db_session.flush()
    asset = CatalogAsset(
        catalog_id=catalog.id, uploaded_by=provider_user.id,
        file_name="test.txt", file_path="uploads/catalogs/1/test.txt",
        file_size=100, file_type="text/plain",
    )
    db_session.add(asset)
    db_session.flush()
    demand = Demand(
        catalog_id=catalog.id, requester_id=agg_user.id,
        provider_id=provider_user.id, title="test",
        purpose="test", delivery_plan="online",
        status=DemandStatus.DATA_UPLOADED,
    )
    db_session.add(demand)
    db_session.commit()

    resp = aggregator.post("/api/tasks", json={
        "demand_id": demand.id,
        "input_asset_ids": [asset.id],
        "task_type": "unknown_type",
        "config": {},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "queued"
    assert data["processor_id"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest apps/api/tests/test_dispatch.py -v`
Expected: FAIL

- [ ] **Step 3: Create dispatch_service.py**

Create `apps/api/app/services/dispatch_service.py`:

```python
import logging
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.processor import Processor, ProcessorStatus
from app.db.models.task import ProcessingTask, TaskStatus
from app.services.processor_service import get_online_processor_by_task_type

logger = logging.getLogger(__name__)

DISPATCH_TIMEOUT = 10


def try_dispatch(db: Session, *, task: ProcessingTask, input_asset_ids: list[int]) -> None:
    processor = get_online_processor_by_task_type(db, task.task_type)
    if processor is None:
        return

    from app.db.models.catalog_asset import CatalogAsset

    assets = db.query(CatalogAsset).filter(CatalogAsset.id.in_(input_asset_ids)).all()
    upload_root = Path(settings.upload_root).resolve()
    output_dir = str(upload_root / "delivery" / f"task_{task.id}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    payload = {
        "task_id": task.id,
        "task_type": task.task_type,
        "callback_base_url": f"http://localhost:8000",
        "input_files": [
            {
                "asset_id": asset.id,
                "file_name": asset.file_name,
                "file_path": str(upload_root / Path(asset.file_path).relative_to("uploads")),
            }
            for asset in assets
        ],
        "config": task.config_json or {},
        "output_dir": output_dir,
    }

    try:
        response = httpx.post(
            f"{processor.endpoint_url}/execute",
            json=payload,
            headers={"Authorization": f"Bearer {processor.api_token}"},
            timeout=DISPATCH_TIMEOUT,
        )
        if response.status_code == 202:
            task.status = TaskStatus.RUNNING
            task.processor_id = processor.id
            logger.info("Task %d dispatched to processor %s", task.id, processor.name)
        else:
            logger.warning("Processor %s returned %d for task %d", processor.name, response.status_code, task.id)
    except httpx.HTTPError as exc:
        logger.warning("Failed to dispatch task %d to processor %s: %s", task.id, processor.name, exc)
```

- [ ] **Step 4: Integrate dispatch into task_service.py**

In `apps/api/app/services/task_service.py`, modify `create_processing_task` to call dispatch after creating the task.

After line `db.add(TaskInputAsset(task_id=task.id, catalog_asset_id=asset_id))` and before `db.commit()`, add:

```python
    from app.services.dispatch_service import try_dispatch
    try_dispatch(db, task=task, input_asset_ids=asset_ids)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest apps/api/tests/test_dispatch.py -v`
Expected: ALL PASS

- [ ] **Step 6: Run all existing tests to verify no regression**

Run: `python -m pytest apps/api/tests/ -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```
git add apps/api/app/services/dispatch_service.py apps/api/app/services/task_service.py apps/api/tests/test_dispatch.py
git commit -m "feat: implement automatic task dispatch to processors"
```

---

### Task 6: Frontend - Processor Types & Admin Page

**Files:**
- Create: `apps/web/src/api/processors.ts`
- Create: `apps/web/src/types/processor.ts`
- Create: `apps/web/src/pages/AdminProcessorPage.vue`
- Modify: `apps/web/src/router/index.ts`
- Modify: `apps/web/src/stores/taskStore.ts`

- [ ] **Step 1: Create processor TypeScript types**

Create `apps/web/src/types/processor.ts`:

```typescript
export interface Processor {
  id: number;
  name: string;
  taskType: string;
  description: string;
  endpointUrl: string;
  status: "online" | "offline";
  lastHeartbeatAt: string;
  registeredAt: string;
}
```

- [ ] **Step 2: Create processor API client**

Create `apps/web/src/api/processors.ts`:

```typescript
import { http } from "./http";
import type { Processor } from "@/types/processor";

export async function fetchProcessors(token: string): Promise<Processor[]> {
  const resp = await http.get("/api/processors", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return (resp.data as any[]).map((item) => ({
    id: item.id,
    name: item.name,
    taskType: item.task_type,
    description: item.description,
    endpointUrl: item.endpoint_url,
    status: item.status,
    lastHeartbeatAt: item.last_heartbeat_at,
    registeredAt: item.registered_at,
  }));
}

export async function fetchOnlineProcessors(token: string): Promise<Processor[]> {
  const all = await fetchProcessors(token);
  return all.filter((p) => p.status === "online");
}
```

- [ ] **Step 3: Create AdminProcessorPage.vue**

Create `apps/web/src/pages/AdminProcessorPage.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchProcessors } from "@/api/processors";
import { getErrorMessage } from "@/api/http";
import StatusPill from "@/components/StatusPill.vue";
import { useSessionStore } from "@/stores/session";
import type { Processor } from "@/types/processor";

const sessionStore = useSessionStore();
const processors = ref<Processor[]>([]);
const loading = ref(false);

async function loadProcessors() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try {
    processors.value = await fetchProcessors(token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

onMounted(loadProcessors);
</script>

<template>
  <div class="page-grid">
    <section class="surface-card">
      <div class="card-head">
        <div><h3>处理器管理</h3><p>查看已注册的外部处理服务及其运行状态。</p></div>
        <div><el-button plain @click="loadProcessors">刷新</el-button></div>
      </div>
      <el-table :data="processors" stripe v-loading="loading">
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="taskType" label="任务类型" width="140" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="endpointUrl" label="端点地址" width="240" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <StatusPill
              :label="row.status === 'online' ? '在线' : '离线'"
              :tone="row.status === 'online' ? 'success' : 'muted'"
            />
          </template>
        </el-table-column>
        <el-table-column prop="lastHeartbeatAt" label="最后心跳" width="180" />
        <el-table-column prop="registeredAt" label="注册时间" width="180" />
      </el-table>
    </section>
  </div>
</template>
```

- [ ] **Step 4: Add route for admin processor page**

In `apps/web/src/router/index.ts`, add after the `/admin/logs` route:

```typescript
    {
      path: "/admin/processors",
      name: "admin-processors",
      component: () => import("@/pages/AdminProcessorPage.vue"),
      meta: {
        auth: true,
        roles: ["admin"],
        title: "处理器管理",
        summary: "管理员查看已注册的外部处理服务。"
      }
    },
```

- [ ] **Step 5: Update TaskRead type to include processor_id**

In `apps/web/src/types/task.ts`, add `processorId` field to the task interface.

- [ ] **Step 6: Commit**

```
git add apps/web/src/api/processors.ts apps/web/src/types/processor.ts apps/web/src/pages/AdminProcessorPage.vue apps/web/src/router/index.ts apps/web/src/types/task.ts
git commit -m "feat: add processor admin page and frontend types"
```

---

### Task 7: Final Integration Verification

- [ ] **Step 1: Run all backend tests**

Run: `python -m pytest apps/api/tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run all frontend tests**

Run: `cd apps/web && npx vitest run`
Expected: ALL PASS (or no regressions from existing tests)

- [ ] **Step 3: Commit any final adjustments**

```
git commit -m "chore: final verification and cleanup"
```
