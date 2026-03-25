"""Application Configuration"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings"""

    # Basic Configuration
    APP_NAME: str = "AiInterviewAgent"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Database Configuration
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis Configuration
    REDIS_URL: str
    REDIS_POOL_SIZE: int = 10

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Celery Configuration
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Aliyun Configuration
    ALIYUN_ACCESS_KEY: str
    ALIYUN_SECRET_KEY: str
    ALIYUN_OSS_BUCKET: str
    ALIYUN_ASR_APPKEY: str
    ALIYUN_TTS_APPKEY: str = ""  # 保留兼容

    # Qwen 通义千问 Configuration (LLM)
    QWEN_API_KEY: str = ""  # DashScope/百炼 API Key，留空则 LLM 使用 fallback
    DASHSCOPE_API_KEY: str = ""  # DashScope Realtime API Key (用于 Qwen3-Omni)
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # DashScope API Base URL

    # XFYun 讯飞星火 TTS Configuration
    XFYUN_APP_ID: str = ""      # 讯飞 APP ID
    XFYUN_APP_KEY: str = ""     # 讯飞 API Key
    XFYUN_APP_SECRET: str = ""  # 讯飞 API Secret
    XFYUN_VOICE: str = "xiaoyan"  # 默认发音人: xiaoyan, xiaofeng, xiaomei, xiaoyu, xiaoxin
    XFYUN_SPEED: int = 50       # 语速: 0-100
    XFYUN_VOLUME: int = 50      # 音量: 0-100
    XFYUN_PITCH: int = 50       # 音调: 0-100

    # TTS Provider Selection
    TTS_PROVIDER: str = "auto"  # auto, xfyun, aliyun, qwen, mock

    # WeChat Mini Program Configuration
    WECHAT_APP_ID: str = ""  # 微信小程序 AppID
    WECHAT_APP_SECRET: str = ""  # 微信小程序 AppSecret

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configuration
    # 注意: 当 allow_credentials=True 时，不能使用 "*" 通配符
    CORS_ORIGINS: list[str] = [
        "http://localhost:3333",
        "http://localhost:3334",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3333",
        "http://127.0.0.1:3334",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_JSON_FORMAT: bool = False
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 10
    LOG_CONSOLE: bool = True

    # SMTP Configuration (Email)
    SMTP_HOST: str = ""  # SMTP server host, e.g., smtp.qq.com
    SMTP_PORT: int = 587  # SMTP server port, 587 for TLS, 465 for SSL
    SMTP_USER: str = ""  # SMTP username (email address)
    SMTP_PASSWORD: str = ""  # SMTP password or app-specific password
    SMTP_FROM: str = ""  # Sender email address
    SMTP_USE_SSL: bool = False  # Use SSL connection (port 465)
    SMTP_USE_TLS: bool = True  # Use TLS connection (port 587)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars (e.g. QWEN_API_KEY) not in model
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
