from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    PACKER = "packer"
    RIDER = "rider"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(default=True)
