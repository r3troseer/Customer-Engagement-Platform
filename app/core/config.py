from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Customer Engagement Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/cep_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://postgres:password@localhost:5432/cep_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Auth — secret owned by Omar; we decode only
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File storage
    STORAGE_BACKEND: str = "local"
    LOCAL_UPLOAD_DIR: str = "./uploads"
    AWS_S3_BUCKET_NAME: str = ""
    AWS_ENDPOINT_URL: str = ""         # Railway Bucket endpoint (leave blank for AWS S3)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "auto"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "CEP Platform"
    EMAILS_FROM_EMAIL: str = "noreply@cep-platform.com"

    # Push notifications
    FCM_SERVER_KEY: str = ""

    # Scheduler
    SCHEDULER_TIMEZONE: str = "Europe/London"
    LEADERBOARD_TOP_N_BONUS: int = 3

    # Compliance alert thresholds (days before expiry)
    CERT_EXPIRY_WARNING_DAYS: int = 30
    CERT_EXPIRY_CRITICAL_DAYS: int = 7

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
