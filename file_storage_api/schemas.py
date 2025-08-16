from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
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
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str
    department_id: int

class User(UserBase):
    id: int
    department_id: int

    class Config:
        orm_mode = True

class UserRoleUpdate(BaseModel):
    role: UserRole

class FileBase(BaseModel):
    name: str
    visibility: VisibilityLevel

class FileCreate(FileBase):
    pass

class FileInfo(FileBase):
    id: int
    size: int
    content_type: str
    owner_id: int
    department_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class FileMetadata(BaseModel):
    pages: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None
    paragraphs: Optional[int] = None
    tables: Optional[int] = None