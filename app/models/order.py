from enum import Enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.db.base import Base, TimestampMixin


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PACKING = "packing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ReservationStatus(str, Enum):
    ACTIVE = "active"
    RELEASED = "released"
    CONSUMED = "consumed"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PENDING)
    total_amount: Mapped[float] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        unique=True, index=True, nullable=False
    )
    checkout_latency_ms: Mapped[Optional[float]] = mapped_column(nullable=True)

    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", lazy="selectin"
    )
    timeline: Mapped[List["OrderStatusHistory"]] = relationship(
        back_populates="order", lazy="selectin"
    )


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(nullable=True)

    order: Mapped["Order"] = relationship(back_populates="timeline")


class FailedOrder(Base, TimestampMixin):
    __tablename__ = "failed_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    store_id: Mapped[int] = mapped_column(nullable=False)
    payload: Mapped[str] = mapped_column(nullable=False)  # JSON dump of request
    error_message: Mapped[str] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(index=True, nullable=False)
    retry_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(
        default="failed"
    )  # e.g., failed, retried, resolved


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price_at_order: Mapped[float] = mapped_column(nullable=False)
    reservation_expires_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, index=True
    )
    reservation_status: Mapped[ReservationStatus] = mapped_column(
        default=ReservationStatus.ACTIVE, index=True
    )

    order: Mapped["Order"] = relationship(back_populates="items", lazy="select")
