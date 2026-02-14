from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseRepository
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate


class StoreRepository(BaseRepository[Store, StoreCreate, StoreUpdate]):
    async def get_nearby_stores(
        self,
        db: AsyncSession,
        *,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Tuple[Store, float]]:
        # Simple Haversine approximation in SQL
        # 6371 is Earth's radius in km
        distance_query = (
            6371
            * func.acos(
                func.cos(func.radians(latitude))
                * func.cos(func.radians(self.model.latitude))
                * func.cos(func.radians(self.model.longitude) - func.radians(longitude))
                + func.sin(func.radians(latitude))
                * func.sin(func.radians(self.model.latitude))
            )
        ).label("distance")

        query = (
            select(self.model, distance_query)
            .filter(distance_query <= radius_km)
            .order_by("distance")
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.all())


store_repo = StoreRepository(Store)
