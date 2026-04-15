# 数传协同平台

一个面向数据供需协作的全栈平台，支持目录发布、需求流转、任务处理与结果交付，并支持外部处理器通过 HTTP 协议自动接入。

## 功能概览

- 用户与权限：
  - 注册/登录
  - 管理员审批用户
  - 审计日志查询
- 数据目录与需求：
  - 供给方创建并发布数据目录
  - 需求方发起并跟踪需求
- 任务与交付：
  - 需求方创建处理任务
  - 任务产物登记与交付下载
- 处理器协议：
  - 外部处理器注册、心跳保活
  - 平台自动派发任务到处理器 `/execute`
  - 处理器回调进度/完成/失败

## 技术栈

- 后端：FastAPI, SQLAlchemy, Alembic, Pydantic
- 前端：Vue 3, Vite, Pinia, Element Plus, Vitest
- 部署：Docker Compose, Nginx, PostgreSQL

## 项目结构

```text
.
├─ apps/
│  ├─ api/                 # FastAPI 后端
│  │  ├─ app/
│  │  ├─ migrations/
│  │  └─ tests/
│  └─ web/                 # Vue 前端
├─ docs/                   # 设计与实施文档
├─ nginx/                  # 反向代理配置
├─ processor-protocol.md   # 外部处理器接入协议
└─ docker-compose.yml
```

## 快速开始（本地开发）

### 1) 启动后端 API

```bash
cd apps/api
python -m pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端健康检查：

```bash
curl http://localhost:8000/health
```

### 2) 初始化管理员账号（可选）

```bash
cd apps/api
python -m app.bootstrap_admin --username admin --password Passw0rd! --email admin@example.com
```

### 3) 启动前端

```bash
cd apps/web
npm install
npm run dev
```

默认前端地址：`http://localhost:5173`默认后端地址：`http://localhost:8000`

> 前端可通过环境变量 `VITE_API_BASE_URL` 指定 API 地址；未设置时默认 `http://localhost:8000`。

## Docker Compose 启动

```bash
docker compose up --build
```

当前 `docker-compose.yml` 包含 `nginx` HTTPS 入口，启动前请准备证书文件：

- `nginx/certs/fullchain.pem`
- `nginx/certs/privkey.pem`

若仅用于本地开发调试，建议优先使用“本地开发”方式分别启动 `api` 与 `web`。

## 环境变量

后端示例配置在：

- `apps/api/.env.example`

本地开发可参考当前项目中的：

- `apps/api/.env`

关键项：

- `DATABASE_URL`：数据库连接
- `SECRET_KEY`：JWT 签名密钥
- `UPLOAD_ROOT`：上传与交付根目录
- `FRONTEND_ORIGINS`：CORS 白名单

## 测试

后端：

```bash
cd apps/api
python -m pytest tests -q
```

前端：

```bash
cd apps/web
npm run test
```

## 外部处理器接入

处理器接入协议详见：

- `processor-protocol.md`

该协议定义了注册、心跳、任务派发和任务回调（progress/complete/fail）等接口。

## `test` 加法器处理器（接口联调用）

项目内置了一个用于验证平台处理器链路的测试处理器：

- 代码：`apps/api/app/test_processor_service.py`
- 默认 `task_type`：`test`
- 输入：文本文件，每行两个数字，空格分隔
- 输出：`result.txt`（每行一个求和结果）

启动命令：

```bash
cd apps/api
uvicorn app.test_processor_service:app --host 0.0.0.0 --port 9000
```

可选环境变量：

- `TEST_PROCESSOR_PLATFORM_URL`（默认 `http://localhost:8000`）
- `TEST_PROCESSOR_ENDPOINT_URL`（默认 `http://localhost:9000`）
- `TEST_PROCESSOR_TASK_TYPE`（默认 `test`）
- `TEST_PROCESSOR_HEARTBEAT_INTERVAL`（默认 `30`）
