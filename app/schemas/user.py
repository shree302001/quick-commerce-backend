from typing import Optional
from pydantic import EmailStr
from app.schemas.base import BaseSchema
from app.models.user import UserRole


class UserBase(BaseSchema):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.CUSTOMER
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
