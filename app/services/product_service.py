from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.product_repo import product_repo
from app.models.product import Product


class ProductService:
    async def get_products(
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
        return await product_repo.get_multi_with_filters(
            db,
            skip=skip,
            limit=limit,
            name=name,
            sku=sku,
            category_id=category_id,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    async def get_product(self, db: AsyncSession, product_id: int) -> Optional[Product]:
        return await product_repo.get(db, id=product_id)


product_service = ProductService()
