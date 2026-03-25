"""应用配置管理"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"  # 允许额外的配置字段
    )

    # 应用信息
    APP_NAME: str = "Recommendation API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Milvus 配置
    MILVUS_HOST: str = "milvus-standalone"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "resources"

    # PostgreSQL 配置 (主数据库)
    DATABASE_URL: str = "postgresql+asyncpg://rec:rec123@postgres:5432/recommendation"

    # Redis 配置
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_STREAM_NAME: str = "rec:tasks"
    REDIS_GROUP_NAME: str = "workers"

    # 模型配置
    MODEL_PATH: str = "/app/models"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM: int = 384

    # Worker 配置
    WORKER_CONCURRENCY: int = 10

    # 日志配置
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()
