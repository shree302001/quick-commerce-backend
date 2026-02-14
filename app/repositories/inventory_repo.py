from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.repository import BaseRepository
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate


class InventoryRepository(BaseRepository[Inventory, InventoryCreate, InventoryUpdate]):
    async def get_by_product_and_store(
        self, db: AsyncSession, *, product_id: int, store_id: int
    ) -> Optional[Inventory]:
        result = await db.execute(
            select(Inventory).filter(
                Inventory.product_id == product_id, Inventory.store_id == store_id
            )
        )
        return result.scalars().first()

    async def get_by_product_and_store_for_update(
        self, db: AsyncSession, *, product_id: int, store_id: int
    ) -> Optional[Inventory]:
        result = await db.execute(
            select(Inventory)
            .filter(Inventory.product_id == product_id, Inventory.store_id == store_id)
            .with_for_update()
        )
        return result.scalars().first()

    async def get_by_store(
        self, db: AsyncSession, *, store_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Inventory], int]:
        query = select(Inventory).filter(Inventory.store_id == store_id)
        count_query = (
            select(func.count())
            .select_from(Inventory)
            .filter(Inventory.store_id == store_id)
        )

        total_count = (await db.execute(count_query)).scalar_one()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count

    async def get_low_stock(
        self, db: AsyncSession, *, threshold: int = 10, store_id: Optional[int] = None
    ) -> List[Inventory]:
        query = select(Inventory).filter(
            (Inventory.quantity - Inventory.reserved_quantity) <= threshold
        )
        if store_id:
            query = query.filter(Inventory.store_id == store_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def aggregate_stock(self, db: AsyncSession, *, product_id: int) -> int:
        query = select(
            func.sum(Inventory.quantity - Inventory.reserved_quantity)
        ).filter(Inventory.product_id == product_id)
        result = await db.execute(query)
        return result.scalar() or 0


inventory_repo = InventoryRepository(Inventory)
