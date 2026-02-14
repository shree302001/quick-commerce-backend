from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema
from app.models.order import OrderStatus, ReservationStatus


class OrderItemBase(BaseSchema):
    product_id: int
    quantity: int


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    price_at_order: float
    reservation_expires_at: Optional[datetime] = None
    reservation_status: ReservationStatus


class OrderBase(BaseSchema):
    user_id: Optional[int] = None
    store_id: Optional[int] = None
    status: Optional[OrderStatus] = OrderStatus.PENDING
    total_amount: Optional[float] = 0.0
    idempotency_key: Optional[str] = None


class OrderCreate(OrderBase):
    user_id: int
    store_id: int
    items: List[OrderItemCreate]
    idempotency_key: str


class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None


class OrderStatusHistoryResponse(BaseSchema):
    status: OrderStatus
    timestamp: datetime
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    created_at: datetime
    items: List[OrderItemResponse]
    timeline: List[OrderStatusHistoryResponse] = []
    checkout_latency_ms: Optional[float] = None


class OrderListResponse(BaseSchema):
    items: List[OrderResponse]
    total: int
    skip: int
    limit: int


class StoreLoadMetrics(BaseSchema):
    store_id: int
    pending_orders_count: int
    active_orders_count: int  # e.g., packing or shipping
    recent_velocity_per_min: float
    total_load_score: float  # calculated heuristic
