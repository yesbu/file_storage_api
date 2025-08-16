from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Literal
from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class VisibilityLevel(str, Enum):
    PRIVATE = "PRIVATE"
    DEPARTMENT = "DEPARTMENT"
    PUBLIC = "PUBLIC"

class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str
    department_id: int

class UserOut(UserBase):
    id: int
    department_id: int

    class Config:
        from_attributes = True

class FileMetadataOut(BaseModel):
    pages: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None

class FileOut(BaseModel):
    id: int
    name: str
    size: int
    visibility: VisibilityLevel
    owner_id: int
    metadata: Optional[FileMetadataOut] = None

    class Config:
        from_attributes = True