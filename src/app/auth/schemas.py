from pydantic import BaseModel, EmailStr
from ..common.enums import Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    department: str


class UserCreate(UserBase):
    password: str
    role: Role = Role.USER


class UserOut(UserBase):
    id: int
    role: Role

    class Config:
        from_attributes = True


class LoginIn(BaseModel):
    email: EmailStr
    password: str
