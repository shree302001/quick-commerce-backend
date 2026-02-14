from typing import Optional
from app.schemas.base import BaseSchema


class StoreBase(BaseSchema):
    name: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = True


class StoreCreate(StoreBase):
    name: str


class StoreUpdate(StoreBase):
    pass


class StoreResponse(StoreBase):
    id: int
