# 数据流转与指令生成系统

当前仓库包含阶段一的最小可运行骨架：

- `apps/api`：`FastAPI` 后端
- `apps/web`：`Vue 3 + TypeScript + Vite + Element Plus` 前端
- `docker-compose.yml`：`postgres + api + web + nginx` 编排入口
- `nginx/default.conf`：实验室服务器对外入口代理

## HTTPS 前置要求

- 面向实验室服务器外网访问时，最终入口必须是全站 HTTPS，不要把仅监听 `80` 的临时配置当成最终部署口径。
- 当前 `docker-compose.yml` 与 `nginx/default.conf` 默认由仓库内的 `nginx` 容器完成 TLS 终止：`80` 端口只做跳转，`443` 端口提供正式入口。
- 部署前至少需要准备：
  - 可从外网访问的域名或固定公网地址
  - `nginx/certs/fullchain.pem`
  - `nginx/certs/privkey.pem`
  - 已替换 `apps/api/.env.example` 里所有占位凭证的部署配置
- `apps/api/.env.example` 中的 `HTTPS_TERMINATION_ENABLED` 用来记录是否由当前入口代理做 TLS 终止。当前仓库里的 `nginx/default.conf` 以 `true` 为默认前提；如果实验室已有上游 LB/WAF 代做 HTTPS，需要同步调整当前 Nginx 配置与端口暴露方式。

## 后端安装、迁移与管理员初始化

1. `cd apps/api`
2. `python -m pip install --upgrade pip`
3. `python -m pip install -e .[dev]`
4. 新建 `apps/api/.env`，至少写入下面这些当前后端已支持的键：

```env
APP_NAME=data-platform-api
API_PREFIX=/api
DATABASE_URL=postgresql+psycopg://<db-user>:<db-password>@localhost:5432/<db-name>
SECRET_KEY=<replace-with-long-random-jwt-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

5. `python -m alembic upgrade head`
6. `python -m app.bootstrap_admin --username admin --password "<部署时生成的强密码>" --email admin@example.com`
7. `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

说明：

- 不要把 `.env.example` 原样复制成 `.env`。它既覆盖了数据库、JWT、上传目录、前端来源和 HTTPS 终止等部署保留项，也包含当前后端设置对象还没有读取的键。
- 当前仓库里 `apps/api/alembic.ini` 与迁移目录已经存在；但 `apps/api/app/bootstrap_admin.py` 仍未合入，所以第 6 步现在会直接失败，这是当前实现未闭环造成的显式阻塞。
- 管理员账号用于系统配置、审批和运营维护；交付结果的 delivery/download 只给 consumer，admin 不作为交付结果消费者。

## 前端启动

1. `cd apps/web`
2. `npm install`
3. `npm run dev`

## Docker Compose 部署

1. 编辑 `apps/api/.env.example`，把其中的数据库密码、JWT 密钥、对外域名和前端来源替换成实验室环境真实值。
2. 准备 TLS 证书文件：
   - `nginx/certs/fullchain.pem`
   - `nginx/certs/privkey.pem`
3. 在仓库根目录执行 `docker compose build`
4. 运行 `docker compose config`
5. 启动服务：`docker compose up -d`
6. 对外访问 `https://<实验室域名>`
7. `http://<实验室域名>` 会被重定向到 `https://<实验室域名>`
8. 后端健康检查地址：`https://<实验室域名>/api/health`
