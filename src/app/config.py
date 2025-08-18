from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App settings
    app_name: str = Field(default="FileVault", alias="APP_NAME")
    debug: bool = Field(default=True, alias="APP_DEBUG")
    secret_key: str = Field(default="change_me", alias="APP_SECRET")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Database
    pg_host: str = Field(default="db", alias="POSTGRES_HOST")
    pg_port: int = Field(default=5432, alias="POSTGRES_PORT")
    pg_db: str = Field(default="filevault", alias="POSTGRES_DB")
    pg_user: str = Field(default="filevault", alias="POSTGRES_USER")
    pg_password: str = Field(default="filevault", alias="POSTGRES_PASSWORD")

    # Redis
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # MinIO
    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_bucket_files: str = Field(default="filevault", alias="MINIO_BUCKET_FILES")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    # Auth
    jwt_algorithm: str = "HS256"
    refresh_token_expire_days: int = 30

    # Bootstrap admin
    bootstrap_admin_email: str = Field(default="admin@example.com", alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_password: str = Field(default="admin123", alias="BOOTSTRAP_ADMIN_PASSWORD")
    bootstrap_admin_department: str = Field(default="HQ", alias="BOOTSTRAP_ADMIN_DEPARTMENT")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

def sync_db_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.pg_user}:{settings.pg_password}"
        f"@{settings.pg_host}:{settings.pg_port}/{settings.pg_db}"
    )
