# 项目文档

这里保留当前仍然需要开发者阅读的文档。

## 文档入口

- [后端开发文档](e:/hanphonejan/Ai-Interview-Agent/docs/backend.md)
- [前端开发文档](e:/hanphonejan/Ai-Interview-Agent/docs/frontend.md)
- [生产部署说明](e:/hanphonejan/Ai-Interview-Agent/deploy/README.md)

## 开发模式

### 本地开发

- 前后端代码本地运行
- PostgreSQL、Redis、Milvus 通过 Docker 提供

常用命令：

```powershell
.\start-infra.ps1
.\start-infra.ps1 -Health
.\start-dev.ps1
```

### 生产部署

- 生产部署相关文件统一放在 `deploy/`
- 使用 `deploy/docker-compose.yml` 启动完整 Docker 栈

## 数据初始化

数据库初始化统一通过以下两个脚本完成：

1. `fastapi/migrate_db.py`
2. `fastapi/scripts/seed_db.py`

`seed_db.py` 会只读使用 `archive/django/interview_2026-02-13_pgsql_data.sql` 导入种子数据，不会修改归档文件。

## 归档说明

历史 Django 资料保留在 `archive/`，视为只读归档。
