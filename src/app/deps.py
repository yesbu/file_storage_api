import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .auth.models import User
from .database import get_session
from .auth.security import decode_token
from .common.enums import Role

class JWTBearer(HTTPBearer):
    def init(self, auto_error: bool = True):
        super(JWTBearer, self).init(auto_error=auto_error)

    async def call(self, request: Request):
        http_credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).call(request)
        return http_credentials.credentials


jwt_bearer = JWTBearer()
async def get_current_user(token: str = Depends(jwt_bearer), session: AsyncSession = Depends(get_session)) -> User:
    logger = logging.getLogger('logger')
    logger.info("token", token)
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="email not found")
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
def require_role(*roles: Role):
    async def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker
