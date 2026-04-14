# Catalog Ingest Multi-File Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把一期主链路切换为“建目录即上传多个文件、按目录申请、获批后按文件勾选处理”。

**Architecture:** 后端新增目录文件实体与任务输入关联表，把原始文件主归属从 `Demand` 迁移到 `Catalog`。前端把目录创建接口改为 `multipart/form-data`，在目录页管理目录文件，在处理页按需求加载对应目录文件并支持多选。

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pytest, Vue 3, Pinia, Element Plus, Vitest

---

## 文件边界

### 后端模型与迁移

- Create: `apps/api/app/db/models/catalog_asset.py`
- Modify: `apps/api/app/db/models/__init__.py`
- Modify: `apps/api/app/db/models/catalog.py`
- Modify: `apps/api/app/db/models/task.py`
- Create: `apps/api/migrations/versions/20260412_0006_catalog_assets_and_task_inputs.py`

### 后端服务与接口

- Modify: `apps/api/app/api/routes/catalogs.py`
- Create: `apps/api/app/schemas/catalog_asset.py`
- Modify: `apps/api/app/schemas/catalog.py`
- Modify: `apps/api/app/schemas/task.py`
- Modify: `apps/api/app/services/catalog_service.py`
- Modify: `apps/api/app/services/demand_service.py`
- Modify: `apps/api/app/services/task_service.py`
- Modify: `apps/api/app/services/file_storage.py`
- Modify: `apps/api/app/api/router.py`
- Optional remove or stop using: `apps/api/app/api/routes/assets.py`

### 前端目录页

- Modify: `apps/web/src/api/catalogs.ts`
- Create: `apps/web/src/api/catalogAssets.ts`
- Modify: `apps/web/src/types/catalog.ts`
- Create: `apps/web/src/types/catalogAsset.ts`
- Modify: `apps/web/src/stores/catalogStore.ts`
- Modify: `apps/web/src/pages/CatalogPage.vue`

### 前端处理页

- Modify: `apps/web/src/api/tasks.ts`
- Modify: `apps/web/src/types/task.ts`
- Modify: `apps/web/src/stores/taskStore.ts`
- Modify: `apps/web/src/stores/demandStore.ts`
- Modify: `apps/web/src/pages/ProcessingPage.vue`
- Modify: `apps/web/src/pages/DemandPage.vue`

### 测试

- Modify: `apps/api/tests/test_catalog_api.py`
- Modify: `apps/api/tests/test_demand_api.py`
- Modify: `apps/api/tests/test_task_api.py`
- Create or modify: `apps/web/src/**/*.spec.ts`

## Task 1: 后端模型与迁移

**Owner:** Implementer 1

**Files:**
- Create: `apps/api/app/db/models/catalog_asset.py`
- Modify: `apps/api/app/db/models/catalog.py`
- Modify: `apps/api/app/db/models/task.py`
- Create: `apps/api/migrations/versions/20260412_0006_catalog_assets_and_task_inputs.py`

- [ ] **Step 1: 写失败测试，锁定新的数据结构**

```python
def test_provider_can_create_catalog_with_multiple_assets(...):
    response = provider_client.post(
        "/api/catalogs",
        files=[
            ("files", ("a.jsonl", BytesIO(b"{}"), "application/json")),
            ("files", ("b.jsonl", BytesIO(b"{}"), "application/json")),
        ],
        data={...},
    )
    assert response.status_code == 201
    assert response.json()["asset_count"] == 2
```

- [ ] **Step 2: 先让迁移表达出最终结构**

```python
op.create_table(
    "catalog_assets",
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("catalogs.id"), nullable=False),
    sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    ...
)
op.create_table(
    "task_input_assets",
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("task_id", sa.Integer(), sa.ForeignKey("processing_tasks.id"), nullable=False),
    sa.Column("catalog_asset_id", sa.Integer(), sa.ForeignKey("catalog_assets.id"), nullable=False),
)
```

- [ ] **Step 3: 最小实现模型**

```python
class CatalogAsset(Base):
    __tablename__ = "catalog_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey("catalogs.id"), index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
```

- [ ] **Step 4: 运行针对性测试与迁移**

```bash
cd apps/api
python -m pytest tests/test_catalog_api.py -q
python -m alembic upgrade head
```

- [ ] **Step 5: 自检**

```text
确认 ProcessingTask 不再依赖 uploaded_assets.id 作为唯一输入。
确认迁移可在空库直接执行到 head。
```

## Task 2: 后端目录文件接口与需求状态切换

**Owner:** Implementer 2

**Files:**
- Modify: `apps/api/app/services/file_storage.py`
- Modify: `apps/api/app/services/catalog_service.py`
- Modify: `apps/api/app/api/routes/catalogs.py`
- Modify: `apps/api/app/services/demand_service.py`
- Create: `apps/api/app/schemas/catalog_asset.py`
- Modify: `apps/api/app/schemas/catalog.py`

- [ ] **Step 1: 写失败测试，锁定目录多文件主链路**

```python
def test_approved_demand_can_read_catalog_assets(...):
    approve = provider_client.post(f"/api/demands/{demand_id}/approve", json={"review_note": "通过"})
    assert approve.json()["status"] == "data_uploaded"
    assets = aggregator_client.get(f"/api/catalogs/{catalog_id}/assets")
    assert assets.status_code == 200
```

- [ ] **Step 2: 扩展文件存储服务**

```python
def save_catalog_upload(*, catalog_id: int, upload: UploadFile) -> dict[str, object]:
    relative_path = PurePosixPath("uploads", "catalogs", str(catalog_id), stored_name)
```

- [ ] **Step 3: 实现目录创建、追加、删除、列表服务**

```python
def create_catalog(db: Session, *, payload: CatalogCreateForm, files: list[UploadFile], provider_id: int) -> Catalog:
    if not files:
        raise HTTPException(status_code=422, detail="至少上传一个文件")
```

- [ ] **Step 4: 审批需求时直接切到可处理状态**

```python
if not catalog_has_assets(db, catalog_id=demand.catalog_id):
    raise HTTPException(status_code=409, detail="目录下无可用文件")
demand.status = DemandStatus.DATA_UPLOADED
```

- [ ] **Step 5: 运行测试**

```bash
cd apps/api
python -m pytest tests/test_catalog_api.py tests/test_demand_api.py -q
```

## Task 3: 后端任务多文件输入

**Owner:** Implementer 3

**Files:**
- Modify: `apps/api/app/schemas/task.py`
- Modify: `apps/api/app/services/task_service.py`
- Modify: `apps/api/app/api/routes/tasks.py`
- Modify: `apps/api/tests/test_task_api.py`

- [ ] **Step 1: 写失败测试，锁定多文件输入**

```python
def test_aggregator_can_create_task_with_multiple_catalog_assets(...):
    response = aggregator_client.post(
        "/api/tasks",
        json={
            "demand_id": demand_id,
            "input_asset_ids": [asset_a_id, asset_b_id],
            "task_type": "instruction",
            "config": {"model": "Qwen-2.5-72B"},
        },
    )
    assert response.status_code == 201
    assert response.json()["input_asset_ids"] == [asset_a_id, asset_b_id]
```

- [ ] **Step 2: 改 schema**

```python
class TaskCreate(BaseModel):
    demand_id: int
    input_asset_ids: list[int]
    task_type: str
    config: dict[str, str]
```

- [ ] **Step 3: 改服务层校验与关联写入**

```python
if not payload.input_asset_ids:
    raise HTTPException(status_code=422, detail="至少选择一个输入文件")
```

```python
for asset in assets:
    db.add(TaskInputAsset(task_id=task.id, catalog_asset_id=asset.id))
```

- [ ] **Step 4: 让任务列表响应带回输入文件 ID**

```python
TaskRead(
    ...,
    input_asset_ids=[item.catalog_asset_id for item in task.input_assets],
)
```

- [ ] **Step 5: 运行测试**

```bash
cd apps/api
python -m pytest tests/test_task_api.py -q
```

## Task 4: 前端目录页与目录文件管理

**Owner:** Implementer 4

**Files:**
- Modify: `apps/web/src/api/catalogs.ts`
- Create: `apps/web/src/api/catalogAssets.ts`
- Modify: `apps/web/src/types/catalog.ts`
- Create: `apps/web/src/types/catalogAsset.ts`
- Modify: `apps/web/src/stores/catalogStore.ts`
- Modify: `apps/web/src/pages/CatalogPage.vue`

- [ ] **Step 1: 写失败测试，锁定 FormData 多文件提交**

```ts
await createCatalog(
  {
    name: "课程论坛问答集",
    files: [fileA, fileB]
  },
  token
);
expect(fetchMock).toHaveBeenCalledWith(
  expect.anything(),
  expect.objectContaining({ body: expect.any(FormData) })
);
```

- [ ] **Step 2: 把目录创建接口改成 FormData**

```ts
const formData = new FormData();
for (const file of payload.files) {
  formData.append("files", file);
}
```

- [ ] **Step 3: 增加目录文件管理 API 与 store 状态**

```ts
assetsByCatalogId: Record<number, CatalogAssetItem[]>;
```

- [ ] **Step 4: 改目录页**

```vue
<el-upload
  :auto-upload="false"
  multiple
  :on-change="handleFileChange"
/>
```

- [ ] **Step 5: 运行测试**

```bash
cd apps/web
npm run test -- src/test/main.spec.ts src/utils/catalogPresentation.spec.ts
```

## Task 5: 前端处理页切换为目录文件多选

**Owner:** Implementer 5

**Files:**
- Modify: `apps/web/src/api/tasks.ts`
- Modify: `apps/web/src/types/task.ts`
- Modify: `apps/web/src/stores/taskStore.ts`
- Modify: `apps/web/src/stores/demandStore.ts`
- Modify: `apps/web/src/pages/ProcessingPage.vue`
- Modify: `apps/web/src/pages/DemandPage.vue`

- [ ] **Step 1: 写失败测试，锁定多文件任务创建**

```ts
await createTask(
  {
    demandId: 3,
    inputAssetIds: [11, 12],
    taskType: "instruction",
    config: { model: "Qwen-2.5-72B" }
  },
  token
);
expect(body.input_asset_ids).toEqual([11, 12]);
```

- [ ] **Step 2: 调整任务类型**

```ts
export interface TaskCreatePayload {
  demandId: number;
  inputAssetIds: number[];
  taskType: string;
  config: Record<string, string>;
}
```

- [ ] **Step 3: 处理页加载目录文件并支持多选**

```vue
<el-table :data="availableAssets" @selection-change="handleSelectionChange">
  <el-table-column type="selection" width="48" />
</el-table>
```

- [ ] **Step 4: 需求页文案改为“按目录申请”**

```ts
const label = `${item.id} - ${item.title} / ${formatCatalogSelection(item)}`
```

- [ ] **Step 5: 运行测试与构建**

```bash
cd apps/web
npm run test -- src/test/main.spec.ts src/utils/catalogPresentation.spec.ts src/stores/__tests__/session.spec.ts src/stores/__tests__/navigation.spec.ts
npm run build
```

## Task 6: 审计与集成验证

**Owner:** Auditor 1 + Auditor 2 + Controller

**Files:**
- Review only: backend/catalog/task related changes
- Review only: frontend/catalog/processing related changes

- [ ] **Step 1: 后端审计**

```text
核对目录文件权限、删除限制、任务输入校验、需求状态切换是否完全符合 spec。
```

- [ ] **Step 2: 前端审计**

```text
核对目录页是否真的支持多文件、文件管理是否可见、处理页是否为多选而不是单选。
```

- [ ] **Step 3: 主进程整体验证**

```bash
cd apps/api
python -m pytest
python -m alembic upgrade head

cd ..\\web
npm run test -- src/test/main.spec.ts src/utils/catalogPresentation.spec.ts src/stores/__tests__/session.spec.ts src/stores/__tests__/navigation.spec.ts
npm run build
```

- [ ] **Step 4: 手工回归点**

```text
1. 提供者建目录时可一次选择多个文件。
2. 提供者可在目录详情继续追加/删除文件。
3. 汇聚者申请目录后，获批即可在处理页看到目录文件。
4. 汇聚者可勾选多个文件创建任务。
```

## 自检

- spec 覆盖检查：目录建档上传、多文件、按目录申请、按文件勾选、后续追加/删除、删除限制、任务多文件输入都已有任务覆盖。
- 占位符检查：无 TBD / TODO / “后续再说”。
- 类型一致性检查：统一使用 `CatalogAsset`、`input_asset_ids`、`asset_count` 这组命名，不再混用旧的单数输入字段。

Plan complete and saved to `docs/superpowers/plans/2026-04-12-catalog-ingest-multi-file.md`. Execution mode is already fixed by user instruction: Subagent-Driven.
