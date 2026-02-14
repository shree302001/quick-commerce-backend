from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.product import ProductResponse, ProductListResponse
from app.services.product_service import product_service
from app.core.logging import add_cache_headers

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def read_products(
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    name: Optional[str] = Query(None, description="Filter products by name"),
    sku: Optional[str] = Query(
        None, description="Filter products by SKU (Exact match, indexed)"
    ),
    category_id: Optional[int] = Query(
        None, description="Filter products by category ID"
    ),
    sort_by: str = Query("id", description="Field to sort by (id, name, price)"),
    sort_desc: bool = Query(False, description="Sort in descending order"),
):
    """
    Retrieve products with pagination, sorting, and filtering.
    """
    products, total = await product_service.get_products(
        db,
        skip=skip,
        limit=limit,
        name=name,
        sku=sku,
        category_id=category_id,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    add_cache_headers(response, max_age=60)
    return {"items": products, "total": total, "skip": skip, "limit": limit}


@router.get("/{product_id}", response_model=ProductResponse)
async def read_product(
    product_id: int,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get a specific product by ID.
    """
    product = await product_service.get_product(db, product_id=product_id)
    if not product:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Product not found")

    add_cache_headers(response, max_age=300)
    return product
