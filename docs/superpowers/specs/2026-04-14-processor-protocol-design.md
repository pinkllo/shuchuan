# 处理器协议设计

## 1. 背景

一期平台的处理任务由汇聚者手动推进状态（queued → running → completed/failed），手动注册产物。这无法满足外部处理服务自动接入的需求。

本设计引入处理器协议（Processor Protocol），让独立的外部处理服务实现一组 HTTP 接口后即可接入平台，平台自动派发任务、接收进度和结果，屏蔽服务内部实现。

## 2. 目标与非目标

### 2.1 目标

- 定义平台与外部处理服务之间的 HTTP REST 协议
- 支持处理器动态注册与心跳保活
- 平台自动将任务派发到对应的在线处理器
- 处理器可上报处理进度、完成结果或失败信息
- 输入输出文件通过本地文件路径共享（同机部署）
- 兼容现有手动模式：无处理器的任务类型仍可手动推进

### 2.2 非目标

- 前端整体重新设计（另立子项目）
- 任务失败自动重试
- 同一 task_type 的多实例负载均衡
- 处理器版本管理
- 跨服务器部署的认证强化

## 3. 角色定义

| 角色 | 说明 |
|---|---|
| 平台（Orchestrator） | 数传平台，管理任务生命周期、派发任务、接收结果 |
| 处理器（Processor） | 外部处理服务，实现协议后可接入平台 |

## 4. 交互流程

```
Processor 启动
  │
  ├──▶ POST /api/processors/register     注册到平台
  │
  │   ... 汇聚者在前端创建处理任务 ...
  │
  ◀── 平台调 Processor 的 POST /execute   派发任务
  │
  │   ... Processor 开始处理 ...
  │
  ├──▶ POST /api/tasks/{id}/progress      上报进度（可多次）
  │
  ├──▶ POST /api/tasks/{id}/complete      处理成功，上报结果文件路径
  │  或
  ├──▶ POST /api/tasks/{id}/fail          处理失败，上报错误信息
  │
  │   ... Processor 定期 ...
  │
  └──▶ POST /api/processors/heartbeat    心跳保活
```

## 5. 数据模型

### 5.1 新增 Processor 表

```
processors
├── id                  主键
├── name                处理器名称（如 "拆书服务"）
├── task_type           对应的任务类型（如 "book_split"），唯一约束
├── description         处理器描述
├── endpoint_url        处理器的 HTTP 地址（如 "http://localhost:9001"）
├── api_token           平台分配的 API Token
├── status              online / offline
├── last_heartbeat_at   最后心跳时间
├── registered_at       注册时间
```

### 5.2 ProcessingTask 扩展

在现有 `ProcessingTask` 模型上新增：

- `processor_id`：关联到处理该任务的 Processor，可为 null（兼容手动模式）

### 5.3 任务类型管理

- `task_type` 由处理器注册时带入，平台自动记录。
- 前端创建任务时展示已有在线处理器支持的 `task_type` 列表，另提供"自定义"选项兼容手动模式。

## 6. 协议接口

### 6.1 平台侧接口（Processor 调用平台）

#### `POST /api/processors/register`

处理器启动时调用，注册自身到平台。

请求体：

```json
{
  "name": "拆书服务",
  "task_type": "book_split",
  "description": "将书籍拆分为章节段落",
  "endpoint_url": "http://localhost:9001"
}
```

响应 201：

```json
{
  "processor_id": 1,
  "api_token": "sp_xxxxxxxxxxxx",
  "message": "注册成功"
}
```

行为：

- 同一 `task_type` 重复注册为幂等更新（更新 endpoint_url 和 description，Token 保持不变）
- 注册成功后 `status` 自动设为 `online`

#### `POST /api/processors/heartbeat`

处理器定期调用，保持在线状态。

请求头： `Authorization: Bearer sp_xxxxxxxxxxxx`

请求体：

```json
{ "processor_id": 1 }
```

响应 200：

```json
{ "status": "ok" }
```

行为：

- 更新 `last_heartbeat_at`
- 超过 60 秒没心跳，平台标记为 `offline`

#### `POST /api/tasks/{task_id}/progress`

处理器在处理过程中调用，上报进度。

请求头： `Authorization: Bearer sp_xxxxxxxxxxxx`

请求体：

```json
{
  "progress": 45,
  "message": "正在处理第 3/7 个文件"
}
```

行为：

- 更新任务的 `progress` 字段
- 更新任务的 `note` 字段为 message 内容
- Token 所属处理器的 `processor_id` 必须与任务的 `processor_id` 匹配

#### `POST /api/tasks/{task_id}/complete`

处理器处理完成后调用，上报结果。

请求头： `Authorization: Bearer sp_xxxxxxxxxxxx`

请求体：

```json
{
  "output_files": [
    {
      "file_path": "uploads/delivery/task_5/result.json",
      "file_name": "result.json",
      "sample_count": 1200
    }
  ],
  "message": "处理完成"
}
```

行为：

- 任务状态设为 `completed`，进度设为 100
- 为每个 output_file 创建 `TaskArtifact` 记录
- `file_path` 必须为相对于项目根目录的相对路径（与现有 TaskArtifact 存储约定一致），平台在 `/execute` 中下发的 `output_dir` 是绝对路径，处理器写入文件后需将路径转换为相对路径再上报
- 若文件路径在 `uploads/delivery/` 下，自动更新需求状态为 `delivered`
- 记录审计日志

#### `POST /api/tasks/{task_id}/fail`

处理器处理失败后调用。

请求头： `Authorization: Bearer sp_xxxxxxxxxxxx`

请求体：

```json
{
  "error": "文件格式不支持",
  "message": "处理失败详情"
}
```

行为：

- 任务状态设为 `failed`
- 任务 `note` 写入错误信息
- 记录审计日志

### 6.2 处理器侧接口（平台调用 Processor）

外部处理服务只需实现一个端点。

#### `POST {endpoint_url}/execute`

平台派发任务时调用。

请求头： `Authorization: Bearer sp_xxxxxxxxxxxx`

请求体：

```json
{
  "task_id": 5,
  "task_type": "book_split",
  "callback_base_url": "http://localhost:8000",
  "input_files": [
    {
      "asset_id": 3,
      "file_name": "book1.txt",
      "file_path": "/abs/path/uploads/catalogs/1/book1.txt"
    },
    {
      "asset_id": 5,
      "file_name": "book2.txt",
      "file_path": "/abs/path/uploads/catalogs/1/book2.txt"
    }
  ],
  "config": { "chapter_mode": "auto" },
  "output_dir": "/abs/path/uploads/delivery/task_5/"
}
```

响应 202：

```json
{ "accepted": true }
```

行为：

- 处理器收到请求后立即返回 202，然后异步开始处理
- 处理过程中用 `callback_base_url + /api/tasks/{task_id}/progress` 上报进度
- 处理完用 `callback_base_url + /api/tasks/{task_id}/complete` 或 `.../fail` 上报结果
- `output_dir` 是平台指定的输出目录，处理器将结果文件写入此处
- 平台在调用前自动创建 `output_dir` 目录

## 7. 安全机制

- 处理器注册时平台分配唯一 API Token（格式 `sp_` 前缀 + 随机字符串）
- 处理器调平台回调接口时必须带 `Authorization: Bearer <token>`
- 平台调处理器 `/execute` 时也带上同一 token，处理器可校验来源
- Token 校验不通过返回 403

## 8. 任务派发逻辑

```
汇聚者创建任务 (POST /api/tasks)
  │
  ├── 查找 task_type 对应的 Processor
  │     ├── 未找到 → 任务照旧创建，status=queued，手动模式
  │     └── 找到 → 检查 Processor 是否 online
  │              ├── offline → 返回 409 错误："处理器离线"
  │              └── online → 创建任务，自动派发
  │
  ├── 向 Processor 发送 POST /execute
  │     ├── 返回 202 → 任务 status=running，记录 processor_id
  │     └── 请求失败/超时 → 任务 status=queued，记录错误日志
  │
  └── 返回任务信息给前端
```

## 9. 异常处理

| 场景 | 处理方式 |
|---|---|
| 派发时 Processor 无响应 | 任务保持 `queued`，日志记录失败原因，前端可重试 |
| Processor 处理中崩溃 | 心跳超时后标记 `offline`，关联的 `running` 任务不自动失败，等管理员处理 |
| Processor 上报了不属于自己的 task_id | Token 校验不通过，返回 403 |
| 重复注册同一 task_type | 更新 endpoint_url 和 description，Token 保持不变 |

## 10. 前端变化（最小改动）

### 10.1 处理页

- 创建任务的 `task_type` 下拉框展示两类选项：
  - 在线处理器类型（带"自动"标识）
  - "自定义"选项（手动模式，兼容旧逻辑）
- 选择自动类型时，创建后无需手动推进状态
- 任务列表新增"处理器"列，展示由哪个处理器执行

### 10.2 管理员处理器列表页（新增）

- 仅 admin 角色可见
- 展示所有已注册处理器：名称、任务类型、状态、端点地址、最后心跳时间
- 只读展示，不提供增删改操作

## 11. 测试要求

### 11.1 后端

- 处理器注册成功与重复注册幂等更新
- 心跳正常更新时间
- Token 校验失败返回 403
- 创建任务时自动匹配在线处理器
- 无处理器时保持手动模式
- 进度上报正确更新任务 progress 和 note 字段
- 完成上报自动创建 TaskArtifact 并更新状态
- 失败上报正确更新任务状态为 failed
- 处理器 offline 时创建任务返回 409

### 11.2 前端

- 创建任务时 task_type 下拉展示在线处理器列表
- 任务列表正确显示处理器名称

## 12. 实施边界

本次做的：

- Processor 数据模型与迁移
- 处理器注册、心跳、状态管理接口
- 平台侧回调接口（progress、complete、fail）
- 任务创建时自动派发逻辑
- 前端处理页最小适配
- 管理员处理器列表页

本次不做的：

- 前端整体重新设计（另立子项目）
- 任务失败自动重试
- 同一 task_type 多实例负载均衡
- 处理器版本管理
- 跨服务器部署的认证强化
