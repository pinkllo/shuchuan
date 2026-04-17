# 数传协同平台 — 外部处理器接入协议 v1

> **用途**：将本文档发送给 AI 或开发者，即可自动编写一个处理器服务并接入平台。
>
> **平台地址**：`http://<PLATFORM_HOST>:8000`（默认本地 `http://localhost:8000`）

---

## 1. 概述

平台允许外部处理器（Processor）通过 HTTP REST 协议自动注册、接收任务、上报进度、汇报结果。

**完整生命周期**：

```
处理器启动 → 注册(获取token) → 心跳保活 → 接收任务 → 上报进度 → 完成/失败 → 循环
```

---

## 2. 注册（Processor → 平台）

处理器启动时调用此接口注册自身。**同一 `task_type` 重复注册会更新信息并生成新 token**。

```
POST /api/processors/register
Content-Type: application/json
```

**请求体**：
```json
{
  "name": "instruction-generator",
  "task_type": "instruction",
  "description": "基于 LLM 的指令数据生成服务",
  "endpoint_url": "http://192.168.1.100:9000"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 处理器显示名称 |
| `task_type` | string | ✅ | 能处理的任务类型（如 `instruction`、`book_split`、`grammar_fix`） |
| `description` | string | ❌ | 可选描述 |
| `endpoint_url` | string | ✅ | 处理器的 HTTP 根地址（平台会向 `{endpoint_url}/execute` 发送任务） |

**响应** `201 Created`：
```json
{
  "processor_id": 1,
  "api_token": "sp_a1b2c3d4e5f6...",
  "message": "注册成功"
}
```

> ⚠️ **必须保存 `api_token`**，后续所有 API 调用都需要它。

---

## 3. 心跳保活（Processor → 平台）

处理器需定期发送心跳（建议每 **30 秒**一次）。超过 **60 秒**无心跳，平台会将处理器标记为离线，不再派发新任务。

```
POST /api/processors/heartbeat
Authorization: Bearer <api_token>
Content-Type: application/json
```

**请求体**：
```json
{
  "processor_id": 1
}
```

**响应** `200 OK`：
```json
{ "status": "ok" }
```

---

## 4. 接收任务（平台 → Processor）

当用户在平台上创建任务且 `task_type` 匹配到在线处理器时，平台会自动向处理器的 **`POST {endpoint_url}/execute`** 发送请求。

**平台发出的请求**：
```
POST http://<你的endpoint_url>/execute
Authorization: Bearer <api_token>
Content-Type: application/json
```

**请求体**：
```json
{
  "task_id": 42,
  "task_type": "instruction",
  "callback_base_url": "http://localhost:8000",
  "input_files": [
    {
      "asset_id": 7,
      "file_name": "train_data.jsonl",
      "file_path": "D:/数传/uploads/catalogs/1/train_data.jsonl"
    }
  ],
  "config": {
    "model": "Qwen-2.5-72B",
    "promptTemplate": "标准问答模板",
    "batchSize": "32"
  },
  "output_dir": "D:/数传/uploads/delivery/task_42"
}
```

| 字段 | 说明 |
|------|------|
| `task_id` | 平台任务 ID，回调时必须带上 |
| `task_type` | 任务类型 |
| `callback_base_url` | 平台 API 的根地址（用于拼接回调 URL） |
| `input_files` | 输入文件列表，`file_path` 是服务器上的绝对路径 |
| `config` | 用户设置的自定义参数（键值对字典） |
| `output_dir` | 建议的输出目录（已自动创建），将输出文件写入此处 |

**你的处理器必须返回**：
- `202 Accepted` — 表示接受任务，开始处理
- 其他状态码 — 平台会记录派发失败，任务保持 `queued` 状态

```json
// 返回 202 即可，body 可选
{ "status": "accepted" }
```

---

## 5. 上报进度（Processor → 平台）

处理过程中，可多次调用此接口更新进度。

```
POST {callback_base_url}/api/tasks/{task_id}/progress
Authorization: Bearer <api_token>
Content-Type: application/json
```

**请求体**：
```json
{
  "progress": 65,
  "message": "已处理 650/1000 条"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `progress` | int (0-100) | 进度百分比 |
| `message` | string | 可选进度描述 |

**响应** `200 OK`：
```json
{ "task_id": 42, "progress": 65, "status": "running" }
```

---

## 6. 完成任务（Processor → 平台）

处理完成后调用此接口。平台会自动将进度设为 100%，注册输出文件。

```
POST {callback_base_url}/api/tasks/{task_id}/complete
Authorization: Bearer <api_token>
Content-Type: application/json
```

**请求体**：
```json
{
  "output_files": [
    {
      "file_path": "uploads/delivery/task_42/result.jsonl",
      "file_name": "result.jsonl",
      "sample_count": 1000
    }
  ],
  "message": "指令生成完成，共 1000 条"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `output_files` | array | 输出文件列表 |
| `output_files[].file_path` | string | **相对于项目根目录的路径**，以 `uploads/delivery/` 开头的文件会自动标记需求为"已交付"状态 |
| `output_files[].file_name` | string | 文件显示名 |
| `output_files[].sample_count` | int | 输出样本数 (≥0) |
| `message` | string | 可选完成描述 |

**响应** `200 OK`：
```json
{ "task_id": 42, "status": "completed", "progress": 100 }
```

> 💡 **关键**：如果 `file_path` 以 `uploads/delivery/` 开头，平台会自动将关联需求标记为 `delivered`，使用者即可在"交付下载"页面下载。

---

## 7. 报告失败（Processor → 平台）

处理失败时调用此接口。

```
POST {callback_base_url}/api/tasks/{task_id}/fail
Authorization: Bearer <api_token>
Content-Type: application/json
```

**请求体**：
```json
{
  "error": "OutOfMemoryError",
  "message": "输入文件过大，超出 GPU 显存限制"
}
```

**响应** `200 OK`：
```json
{ "task_id": 42, "status": "failed" }
```

---

## 8. 认证说明

所有处理器 → 平台的 API 调用都使用 **Bearer Token** 认证：

```
Authorization: Bearer sp_a1b2c3d4e5f6...
```

Token 在注册时由平台返回，处理器必须安全保存。

---

## 9. 最小实现模板

以下是一个 **Python + FastAPI** 的最小处理器实现骨架，可以直接使用：

```python
"""
数传协同平台 — 外部处理器最小实现模板
启动命令: uvicorn processor:app --host 0.0.0.0 --port 9000
"""
import asyncio
import threading
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

# ─── 配置 ───
PLATFORM_URL = "http://localhost:8000"      # 平台地址
PROCESSOR_NAME = "my-processor"             # 处理器名称
TASK_TYPE = "instruction"                   # 处理的任务类型
ENDPOINT_URL = "http://localhost:9000"      # 本处理器的地址
DESCRIPTION = "自定义指令生成处理器"

# ─── 全局状态 ───
API_TOKEN: str | None = None
PROCESSOR_ID: int | None = None

app = FastAPI()


# ─── 数据模型 ───
class InputFile(BaseModel):
    asset_id: int
    file_name: str
    file_path: str

class ExecuteRequest(BaseModel):
    task_id: int
    task_type: str
    callback_base_url: str
    input_files: list[InputFile]
    config: dict[str, str]
    output_dir: str


# ─── 接收任务 ───
@app.post("/execute", status_code=202)
async def execute(
    request: ExecuteRequest,
    authorization: str = Header(...),
):
    """平台向此端点派发任务。必须返回 202。"""
    # 在后台线程处理，立即返回 202
    threading.Thread(
        target=_process_task,
        args=(request,),
        daemon=True,
    ).start()
    return {"status": "accepted"}


def _process_task(req: ExecuteRequest):
    """实际处理逻辑 — 替换为你的业务代码"""
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    base = req.callback_base_url

    try:
        # 1. 读取输入文件
        all_lines = []
        for f in req.input_files:
            path = Path(f.file_path)
            if path.exists():
                all_lines.extend(path.read_text(encoding="utf-8").splitlines())

        total = len(all_lines)

        # 2. 逐条处理 + 上报进度
        results = []
        for i, line in enumerate(all_lines):
            # ========== 替换为你的处理逻辑 ==========
            results.append(f"processed: {line}")
            # =========================================

            if (i + 1) % max(1, total // 10) == 0:
                progress = int((i + 1) / total * 100)
                httpx.post(
                    f"{base}/api/tasks/{req.task_id}/progress",
                    json={"progress": progress, "message": f"已处理 {i+1}/{total}"},
                    headers=headers,
                    timeout=5,
                )

        # 3. 写入输出文件
        output_dir = Path(req.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "result.jsonl"
        output_file.write_text("\n".join(results), encoding="utf-8")

        # 4. 汇报完成
        httpx.post(
            f"{base}/api/tasks/{req.task_id}/complete",
            json={
                "output_files": [{
                    "file_path": f"uploads/delivery/task_{req.task_id}/result.jsonl",
                    "file_name": "result.jsonl",
                    "sample_count": len(results),
                }],
                "message": f"处理完成，共 {len(results)} 条",
            },
            headers=headers,
            timeout=10,
        )

    except Exception as e:
        # 5. 汇报失败
        httpx.post(
            f"{base}/api/tasks/{req.task_id}/fail",
            json={"error": type(e).__name__, "message": str(e)},
            headers=headers,
            timeout=5,
        )


# ─── 启动时注册 + 心跳 ───
@app.on_event("startup")
async def startup():
    global API_TOKEN, PROCESSOR_ID

    # 注册
    resp = httpx.post(f"{PLATFORM_URL}/api/processors/register", json={
        "name": PROCESSOR_NAME,
        "task_type": TASK_TYPE,
        "description": DESCRIPTION,
        "endpoint_url": ENDPOINT_URL,
    })
    resp.raise_for_status()
    data = resp.json()
    API_TOKEN = data["api_token"]
    PROCESSOR_ID = data["processor_id"]
    print(f"✅ 注册成功: processor_id={PROCESSOR_ID}")

    # 启动心跳
    asyncio.create_task(_heartbeat_loop())


async def _heartbeat_loop():
    while True:
        await asyncio.sleep(30)
        try:
            httpx.post(
                f"{PLATFORM_URL}/api/processors/heartbeat",
                json={"processor_id": PROCESSOR_ID},
                headers={"Authorization": f"Bearer {API_TOKEN}"},
                timeout=5,
            )
        except Exception as e:
            print(f"⚠️  心跳失败: {e}")
```

---

## 10. 接入检查清单

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | 注册 | 启动时调用 `/api/processors/register`，保存返回的 `api_token` |
| 2 | 心跳 | 每 30 秒调用 `/api/processors/heartbeat` |
| 3 | 接收任务 | 实现 `POST /execute` 端点，返回 `202` |
| 4 | 认证 | 验证 `/execute` 请求的 `Authorization` header |
| 5 | 进度上报 | 处理过程中调用 `/api/tasks/{id}/progress` |
| 6 | 完成回调 | 处理完成后调用 `/api/tasks/{id}/complete`，附带输出文件信息 |
| 7 | 失败回调 | 处理失败时调用 `/api/tasks/{id}/fail` |
| 8 | 输出路径 | 文件写入 `output_dir`，`file_path` 以 `uploads/delivery/` 开头触发自动交付 |

---

## 11. 错误码参考

| 状态码 | 场景 |
|--------|------|
| `201` | 注册成功 |
| `200` | 心跳/进度/完成/失败 成功 |
| `403` | Token 无效或与处理器不匹配 |
| `404` | 任务不存在 |
| `409` | 处理器离线 / 状态转换非法 |

---

## 12. `test` 加法器处理器（仓库内可直接运行）

为快速验证平台处理器接口链路，仓库已提供可运行的测试处理器：

- 文件：`apps/api/app/test_processor_service.py`
- `task_type`：默认 `test`
- 功能：读取输入文本文件，按行解析 `两个数字`（空格分割），输出每行和

启动命令（在 `apps/api` 目录）：

```bash
uvicorn app.test_processor_service:app --host 0.0.0.0 --port 9000
```

可选环境变量：

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `TEST_PROCESSOR_PLATFORM_URL` | `http://localhost:8000` | 平台地址 |
| `TEST_PROCESSOR_ENDPOINT_URL` | `http://localhost:9000` | 处理器对外地址（用于注册） |
| `TEST_PROCESSOR_TASK_TYPE` | `test` | 任务类型 |
| `TEST_PROCESSOR_HEARTBEAT_INTERVAL` | `30` | 心跳间隔秒数 |

输入文件格式示例（每行两个数）：

```text
1 2
10 25
3.5 4.5
```

输出文件：`result.txt`（位于平台下发的 `output_dir` 目录）

```text
3
35
8.0
```

---

## 13. [附录] 自定义前端参数表单 (动态 Schema)

工作台（Workbench）不仅支持全自动流转，还支持**根据任务类别自动渲染自定义输入表单**。如果你的外部处理器需要用户指定额外的运行参数（例如切分粒度、重叠Token、模型引擎类型等），你需要配置前端的动态字段，使其能在界面无缝显示。

### 配置方式
平台接收到你注册的 `task_type` 并在前端展示时，会自动去前端的状态管理配置中匹配对应的 Schema 数组。

请前往前端库编辑：`apps/web/src/stores/capabilityStore.ts`

在 `capabilities` 初始数组中，添加或修改对象，使其 `id` 与你的 `task_type` 相同，并注入 `schema` 规范：

```typescript
    {
      id: "my-custom-task",    // 需与 Processor 注册时的 task_type 保持绝对一致
      name: "外部某处理服务",
      description: "在列表展示的功能补充说明卡片",
      selectable: true,
      schema: [
        {
          prop: "chunkSize",
          label: "单块包含字数限制 (Token)",
          type: "input",
          default: "1000",
          placeholder: "不填默认1000"
        },
        {
          prop: "engine",
          label: "处理模型",
          type: "select",
          options: ["Fast-Engine", "Deep-Engine", "Balanced"],
          default: "Balanced"
        }
      ]
    }
```

### 运行时表现
1. 用户在前端网格点选你的任务卡片后，工作台会立刻提取此 `schema` 并顺延展开表单，自动处理了双向绑定与空值校验。
2. 平台最终调用你的处理器 `POST /execute` 时，用户填写的表单内容将**全量打包给 JSON**，并透传进请求体的 `config` 字段中：
   ```json
   "config": {
     "chunkSize": "2000",
     "engine": "Deep-Engine"
   }
   ```

**🌟 免配友好原则**：
如果你无需收集外部用户的任何输入，无需在 `schema` 里配置任何项目甚至可以缺省这个字段。当 Schema 为空时，平台工作台将表现为**参数区结构完全折叠/消失**，实现极简的“零打扰提交执行”。
