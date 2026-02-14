from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.inventory_repo import inventory_repo
from app.models.inventory import Inventory, InventorySnapshot


class InventoryService:
    async def create_snapshot(
        self, db: AsyncSession, inventory: Inventory, reason: str
    ) -> Optional[InventorySnapshot]:
        # Snapshot Sampling: Only log critical events or 1 in every 5 updates
        import random

        is_critical = reason in ["manual_adjustment", "stock_out", "audit_failure"]
        should_sample = random.random() < 0.2  # 20% sampling

        if not is_critical and not should_sample:
            inventory.last_snapshot_at = (
                datetime.utcnow()
            )  # Update timestamp even if no snapshot
            return None

        snapshot = InventorySnapshot(
            inventory_id=inventory.id,
            quantity=inventory.quantity,
            reserved_quantity=inventory.reserved_quantity,
            timestamp=datetime.utcnow(),
            reason=reason,
        )
        db.add(snapshot)
        inventory.last_snapshot_at = snapshot.timestamp
        return snapshot

    async def check_availability(
        self, db: AsyncSession, product_id: int, store_id: int, quantity: int
    ) -> bool:
        inventory = await inventory_repo.get_by_product_and_store(
            db, product_id=product_id, store_id=store_id
        )
        if not inventory:
            return False
        return inventory.available_quantity >= quantity

    async def reserve_stock(
        self, db: AsyncSession, product_id: int, store_id: int, quantity: int
    ) -> Inventory:
        inventory = await inventory_repo.get_by_product_and_store_for_update(
            db, product_id=product_id, store_id=store_id
        )
        if not inventory:
            raise HTTPException(
                status_code=404,
                detail=f"Inventory for product {product_id} not found in store {store_id}",
            )

        if inventory.available_quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {product_id}. Available: {inventory.available_quantity}, Requested: {quantity}",
            )

        # Lock / Reserve
        inventory.reserved_quantity += quantity
        db.add(inventory)

        # Create Snapshot
        await self.create_snapshot(db, inventory, reason="stock_reservation")

        # We DON'T commit here, allowing the caller (e.g. OrderService) to manage the transaction.
        return inventory

    async def get_inventory_by_store(
        self, db: AsyncSession, store_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Inventory], int]:
        return await inventory_repo.get_by_store(
            db, store_id=store_id, skip=skip, limit=limit
        )

    async def get_low_stock_items(
        self, db: AsyncSession, threshold: int = 10, store_id: Optional[int] = None
    ) -> List[Inventory]:
        return await inventory_repo.get_low_stock(
            db, threshold=threshold, store_id=store_id
        )

    async def get_total_available_stock(self, db: AsyncSession, product_id: int) -> int:
        return await inventory_repo.aggregate_stock(db, product_id=product_id)

    async def get_inventory_item(
        self, db: AsyncSession, product_id: int, store_id: int
    ) -> Optional[Inventory]:
        return await inventory_repo.get_by_product_and_store(
            db, product_id=product_id, store_id=store_id
        )

    async def get_snapshots(
        self,
        db: AsyncSession,
        store_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[InventorySnapshot], int]:
        return await inventory_repo.get_snapshots(
            db, store_id=store_id, skip=skip, limit=limit
        )


inventory_service = InventoryService()
