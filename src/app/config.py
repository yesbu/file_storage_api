from pydantic_settings import BaseSettings
from pydantic import Field
class Settings(BaseSettings):
    app_name: str = Field(default="FileVault", alias="APP_NAME")
    debug: bool = Field(default=True, alias="APP_DEBUG")
    secret_key: str = Field(default="change_me", alias="APP_SECRET")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    pg_host: str = Field(default="db", alias="POSTGRES_HOST")
    pg_port: int = Field(default=5432, alias="POSTGRES_PORT")
    pg_db: str = Field(default="filevault", alias="POSTGRES_DB")
    pg_user: str = Field(default="filevault", alias="POSTGRES_USER")
    pg_password: str = Field(default="filevault", alias="POSTGRES_PASSWORD")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    s3_endpoint: str = Field(default="http://minio:9000", alias="S3_ENDPOINT")
    s3_bucket: str = Field(default="files", alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_access_key: str = Field(default="minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin", alias="S3_SECRET_KEY")
    s3_secure: bool = Field(default=False, alias="S3_SECURE")
    jwt_algorithm: str = "HS256"
    refresh_token_expire_days: int = 30
    bootstrap_admin_email: str = Field(default="admin@example.com", alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_password: str = Field(default="admin123", alias="BOOTSTRAP_ADMIN_PASSWORD")
    bootstrap_admin_department: str = Field(default="HQ", alias="BOOTSTRAP_ADMIN_DEPARTMENT")
    class Config:
        env_file = ".env"
settings = Settings()
def sync_db_url() -> str:
    return f"postgresql+asyncpg://{settings.pg_user}:{settings.pg_password}@{settings.pg_host}:{settings.pg_port}/{settings.pg_db}"
