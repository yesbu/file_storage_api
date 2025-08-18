from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_session
from ..auth.models import User
from ..auth.schemas import UserCreate, UserOut
from ..auth.security import hash_password
from ..deps import require_role, get_current_user
from ..common.enums import Role

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserOut, dependencies=[Depends(require_role(Role.MANAGER, Role.ADMIN))])
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    exists = await session.execute(select(User).where(User.email == payload.email))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")
    u = User(email=payload.email, full_name=payload.full_name, department=payload.department, role=payload.role, hashed_password=hash_password(payload.password))
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u

@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role(Role.MANAGER, Role.ADMIN))])
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    u = await session.get(User, user_id)
    if not u:
        raise HTTPException(404, "Not found")
    return u

@router.put("/{user_id}/role", dependencies=[Depends(require_role(Role.MANAGER, Role.ADMIN))])
async def change_role(user_id: int, role: Role, session: AsyncSession = Depends(get_session)):
    u = await session.get(User, user_id)
    if not u:
        raise HTTPException(404, "Not found")
    u.role = role
    await session.commit()
    return {"status": "ok"}
@router.get("/", response_model=list[UserOut])
async def list_department_users(session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    if user.role in (Role.MANAGER, Role.ADMIN):
        res = await session.execute(select(User))
    else:
        res = await session.execute(select(User).where(User.department == user.department))
    return res.scalars().all()

