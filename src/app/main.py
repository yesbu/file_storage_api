from fastapi import FastAPI
from .config import settings
from .database import engine, Base, SessionLocal
from .auth.models import User
from .auth.security import hash_password
from .common.enums import Role
from .auth.routes import router as auth_router
from .files.routes import router as files_router
from .users.routes import router as users_router

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.email == settings.bootstrap_admin_email))
        admin = res.scalar_one_or_none()
        if not admin:
            session.add(User(email=settings.bootstrap_admin_email, full_name="Admin", department=settings.bootstrap_admin_department, role=Role.ADMIN, hashed_password=hash_password(settings.bootstrap_admin_password)))
            await session.commit()

app.include_router(auth_router)
app.include_router(files_router)
app.include_router(users_router)
