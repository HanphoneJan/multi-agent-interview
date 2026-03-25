# 生产部署

生产环境部署相关文件统一放在 `deploy/`。

## 当前文件

- `docker-compose.yml`：生产环境 Docker Compose 入口

## 启动

```powershell
docker compose -f deploy/docker-compose.yml up -d
```

## 停止

```powershell
docker compose -f deploy/docker-compose.yml down
```

## 初始化

容器启动时会自动执行：

1. `fastapi/migrate_db.py`
2. `fastapi/scripts/seed_db.py`

## 说明

- `deploy/` 只放生产部署相关文件
- 本地开发基础设施仍使用根目录 `docker-compose.infra.yml`
