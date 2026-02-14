from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.repository import BaseRepository
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    async def get_by_idempotency_key(
        self, db: AsyncSession, *, idempotency_key: str
    ) -> Optional[Order]:
        result = await db.execute(
            select(Order).filter(Order.idempotency_key == idempotency_key)
        )
        return result.scalars().first()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        store_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
    ) -> Tuple[List[Order], int]:
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        filters = []
        if user_id:
            filters.append(self.model.user_id == user_id)
        if store_id:
            filters.append(self.model.store_id == store_id)
        if status:
            filters.append(self.model.status == status)

        if filters:
            query = query.filter(*filters)
            count_query = count_query.filter(*filters)

        total_count = (await db.execute(count_query)).scalar_one()
        result = await db.execute(
            query.order_by(self.model.id.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total_count

    async def get_store_load_metrics(self, db: AsyncSession, *, store_id: int) -> dict:
        pending_query = (
            select(func.count())
            .select_from(Order)
            .filter(Order.store_id == store_id, Order.status == OrderStatus.PENDING)
        )
        active_query = (
            select(func.count())
            .select_from(Order)
            .filter(
                Order.store_id == store_id,
                Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PACKING]),
            )
        )

        # Smoothed factor: Orders in last 15 minutes
        from datetime import datetime, timedelta

        recent_cutoff = datetime.utcnow() - timedelta(minutes=15)
        recent_query = (
            select(func.count())
            .select_from(Order)
            .filter(Order.store_id == store_id, Order.created_at >= recent_cutoff)
        )

        pending_count = (await db.execute(pending_query)).scalar_one()
        active_count = (await db.execute(active_query)).scalar_one()
        recent_count = (await db.execute(recent_query)).scalar_one()

        # Heuristic: base load + (velocity * constant)
        base_load = pending_count + (active_count * 1.5)
        smoothing_velocity = recent_count / 15.0  # orders per minute

        return {
            "store_id": store_id,
            "pending_orders_count": pending_count,
            "active_orders_count": active_count,
            "recent_velocity_per_min": round(smoothing_velocity, 2),
            "total_load_score": float(base_load + (smoothing_velocity * 5)),
        }


order_repo = OrderRepository(Order)
