"""推荐系统 PostgreSQL 数据库连接管理

注意：此模块现在重定向到主数据库 (app.database) 以统一数据库连接。
保留此文件是为了向后兼容，所有操作实际都在 ai_interview 数据库上执行。
"""
from typing import AsyncGenerator
from sqlalchemy import text

# 重定向到主数据库
from app.database import (
    engine,
    async_session_factory,
    AsyncSessionLocal,
    get_db,
    get_db_context,
    get_async_session,
)

# 为了向后兼容，保留这些导出
__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "get_db_context",
    "get_async_session",
    "init_db",
    "check_db_health",
]


async def init_db():
    """初始化数据库（表由 Alembic 管理，此函数保留用于兼容性）"""
    # 表结构由 Alembic 迁移管理，不需要在这里创建
    pass


async def check_db_health() -> bool:
    """检查数据库连接健康"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
