from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema


class InventoryBase(BaseSchema):
    product_id: Optional[int] = None
    store_id: Optional[int] = None
    quantity: Optional[int] = 0
    reserved_quantity: Optional[int] = 0
    batch_id: Optional[str] = None
    location_id: Optional[str] = None


class InventoryCreate(InventoryBase):
    product_id: int
    store_id: int
    quantity: int


class InventoryUpdate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    id: int
    available_quantity: int


class InventoryListResponse(BaseSchema):
    items: List[InventoryResponse]
    total: int
    skip: int
    limit: int


class AggregateStockResponse(BaseSchema):
    product_id: int
    total_available_quantity: int


class InventorySnapshotResponse(BaseSchema):
    id: int
    inventory_id: int
    product_name: str
    quantity: int
    reserved_quantity: int
    timestamp: datetime
    reason: Optional[str] = None


class InventorySnapshotListResponse(BaseSchema):
    items: List[InventorySnapshotResponse]
    total: int
    skip: int
    limit: int
