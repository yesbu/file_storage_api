from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .auth.models import User
from .database import get_session
from .common.enums import Role


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        http_credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        return http_credentials.credentials


jwt_bearer = JWTBearer()


async def get_current_user(
        session: AsyncSession = Depends(get_session)) -> User:
    email = "admin@example.com"
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found")


def require_role(*roles: Role):
    async def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker
