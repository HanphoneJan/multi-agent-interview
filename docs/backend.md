# 后端开发文档

本文面向日常维护这个项目后端的开发者，目标是让你知道：

- 后端代码放在哪
- 本地怎么启动
- 数据库怎么初始化
- 改代码时先看哪里

## 1. 技术栈

- Python 3.10+
- FastAPI
- SQLAlchemy Core
- Alembic
- PostgreSQL
- Redis
- Celery

后端代码目录：`fastapi/`

## 2. 目录结构

后端核心目录在 `fastapi/app/`：

- `api/`：HTTP 接口
- `services/`：业务逻辑
- `models/`：表定义
- `schemas/`：请求/响应模型
- `core/`：配置、安全、基础能力
- `tasks/`、`workers/`：异步任务
- `tests/`：测试

常用文件：

- `fastapi/app/main.py`：FastAPI 入口
- `fastapi/database.py`：数据库会话
- `fastapi/config.py`：运行配置
- `fastapi/migrate_db.py`：数据库迁移入口
- `fastapi/scripts/seed_db.py`：种子数据导入

## 3. 本地启动方式

推荐顺序：

### 3.1 启动基础设施

在项目根目录执行：

```powershell
.\start-infra.ps1
```

这一步只会启动：

- PostgreSQL
- Redis
- Milvus

### 3.2 初始化开发环境

```powershell
.\start-dev.ps1
```

这一步会：

1. 启动基础设施
2. 创建 `fastapi/.venv`（如果不存在）
3. 安装 Python 依赖
4. 执行数据库迁移
5. 导入种子数据

### 3.3 启动后端服务

```powershell
cd fastapi
.venv\Scripts\python -m uvicorn app.main:app --reload --port 18000
```

如果你还需要 Celery worker：

```powershell
cd fastapi
.venv\Scripts\python -m app.worker_main
```

## 4. 环境变量

后端主要使用 `fastapi/.env`。

最重要的变量有：

- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `JWT_SECRET_KEY`

本地开发时数据库通常指向：

- PostgreSQL：`localhost:15432`
- Redis：`localhost:16379`

注意：

- 你当前环境里如果有全局 `DEBUG=release`，会导致配置解析失败
- `start-dev.ps1` 已经做了兜底

## 5. 数据库初始化规则

数据库初始化只走下面两步：

1. `fastapi/migrate_db.py`
2. `fastapi/scripts/seed_db.py`

其中：

- 表结构由 Alembic 管理
- 种子数据由 `seed_db.py` 导入
- 归档 SQL 在 `archive/`，只读，不允许修改

当前种子数据来源：

- `archive/` 目录下的 SQL 文件

当前内置测试账号：

- `test_new@example.com / Test123456`
- `test_exp@example.com / Test123456`
- `admin@example.com / Admin123456`

## 6. 常见开发入口

如果你要改接口，优先看：

- `fastapi/app/api/v1/`

如果你要改业务逻辑，优先看：

- `fastapi/app/services/`

如果你要改表结构，优先看：

- `fastapi/app/models/`
- `fastapi/alembic/versions/`

如果你要改鉴权或配置，优先看：

- `fastapi/app/core/`
- `fastapi/config.py`

## 7. 常用命令

安装依赖：

```powershell
cd fastapi
.venv\Scripts\pip install -r requirements.txt
```

执行迁移：

```powershell
cd fastapi
.venv\Scripts\python migrate_db.py
```

导入种子数据：

```powershell
cd fastapi
.venv\Scripts\python scripts\seed_db.py
```

运行测试：

```powershell
cd fastapi
.venv\Scripts\python -m pytest
```

手工验证登录流：

```powershell
cd fastapi
.venv\Scripts\python scripts\verify_login_flow.py
```

## 8. 开发建议

- 先确认改动属于 `api`、`services`、`models` 还是 `core`
- 涉及数据库结构时，不要手改数据库，走 Alembic
- 涉及初始化数据时，不要改 `archive/`，改 `seed_db.py`
- 本地调试时优先使用根目录脚本，不要自己拼零散命令
