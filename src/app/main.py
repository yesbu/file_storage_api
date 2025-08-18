import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import settings
from src.app.database import engine, Base, SessionLocal
from src.app.auth.models import User
from src.app.auth.security import hash_password
from src.app.common.enums import Role
from src.app.auth.routes import router as auth_router
from src.app.files.routes import router as files_router
from src.app.users.routes import router as users_router
from src.app.storage.minio_client import get_minio_client

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None
)



@app.get("/health", tags=["healthcheck"])
async def health_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:

    try:
        await db.execute(select(1))
        minio = get_minio_client()
        if not minio.bucket_exists(settings.minio_bucket_files):
            raise HTTPException(
                status_code=503,
                detail="MinIO bucket not available"
            )

        return JSONResponse(
            content={"status": "ok", "version": "1.0.0"},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        admin = await db.execute(
            select(User).where(User.email == settings.bootstrap_admin_email)
        )
        if not admin.scalar_one_or_none():
            db.add(User(
                email=settings.bootstrap_admin_email,
                full_name="Admin",
                department=settings.bootstrap_admin_department,
                role=Role.ADMIN,
                hashed_password=hash_password(settings.bootstrap_admin_password),
            ))
            await db.commit()

    minio = get_minio_client()
    if not minio.bucket_exists(settings.minio_bucket_files):
        minio.make_bucket(settings.minio_bucket_files)

    yield


app.router.lifespan_context = lifespan

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
