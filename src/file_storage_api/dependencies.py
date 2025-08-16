from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models
from .auth import get_current_user
from .database import get_db

def check_file_access(file: models.File, user: models.User) -> bool:
    if user.role == models.UserRole.ADMIN:
        return True
    if file.visibility == models.VisibilityLevel.PUBLIC:
        return True
    if file.visibility == models.VisibilityLevel.DEPARTMENT and user.department_id == file.department_id:
        return True
    if file.owner_id == user.id:
        return True
    return False

def get_current_admin(user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

def get_current_manager(user: models.User = Depends(get_current_user)):
    if user.role not in [models.UserRole.MANAGER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager privileges required"
        )
    return user