from typing import List, Optional, Tuple
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseRepository
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        sku: Optional[str] = None,
        category_id: Optional[int] = None,
        sort_by: Optional[str] = "id",
        sort_desc: bool = False,
    ) -> Tuple[List[Product], int]:
        # Base query
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        # Filters
        filters = []
        if name:
            filters.append(self.model.name.ilike(f"%{name}%"))
        if sku:
            filters.append(self.model.sku == sku)
        if category_id:
            filters.append(self.model.category_id == category_id)

        if filters:
            query = query.filter(*filters)
            count_query = count_query.filter(*filters)

        # Total count
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Sorting logic
        if sort_by and hasattr(self.model, sort_by):
            column = getattr(self.model, sort_by)
            if sort_desc:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(column)

        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count


product_repo = ProductRepository(Product)
