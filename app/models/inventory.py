from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index, Text
from app.db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    batch_id: Mapped[str] = mapped_column(nullable=True)
    location_id: Mapped[str] = mapped_column(nullable=True)
    last_snapshot_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="inventory_items")
    snapshots: Mapped[List["InventorySnapshot"]] = relationship(
        back_populates="inventory"
    )

    __table_args__ = (
        Index("ix_inventory_store_product", "store_id", "product_id"),
        # Partial Index for fast low-stock queries (threshold < 10)
        Index(
            "ix_inventory_low_stock",
            "product_id",
            "store_id",
            postgresql_where="(quantity - reserved_quantity) < 10",
        ),
    )

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    reason: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Relationships
    inventory: Mapped["Inventory"] = relationship(back_populates="snapshots")
