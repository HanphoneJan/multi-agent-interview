# AiInterviewAgent - FastAPI

FastAPI 后端服务。

## 快速开始

```bash
cd fastapi
cp .env.example .env
pip install -r requirements.txt
python migrate_db.py
python scripts/seed_db.py
uvicorn app.main:app --reload
```

## 相关说明

- 项目总览见 [../docs/README.md](../docs/README.md)
- 生产部署见 [../deploy/README.md](../deploy/README.md)
