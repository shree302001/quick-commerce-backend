from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.inventory import (
    InventoryResponse,
    InventoryListResponse,
    AggregateStockResponse,
    InventorySnapshotListResponse,
)
from app.services.inventory_service import inventory_service
from app.core.logging import add_cache_headers

router = APIRouter()


@router.get("/store/{store_id}", response_model=InventoryListResponse)
async def list_store_inventory(
    store_id: int,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """
    List all inventory items for a specific store.
    """
    items, total = await inventory_service.get_inventory_by_store(
        db, store_id=store_id, skip=skip, limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/check", response_model=InventoryResponse)
async def check_product_stock(
    product_id: int = Query(..., description="The ID of the product"),
    store_id: int = Query(..., description="The ID of the store"),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Check current stock levels for a specific product in a specific store.
    """
    inventory = await inventory_service.get_inventory_item(
        db, product_id=product_id, store_id=store_id
    )
    if not inventory:
        raise HTTPException(
            status_code=404, detail="Inventory not found for this product and store"
        )
    return inventory


@router.get("/low-stock", response_model=List[InventoryResponse])
async def detect_low_stock(
    store_id: Optional[int] = Query(None, description="Filter by store"),
    threshold: int = Query(10, description="The threshold for low stock"),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Identify items that are below the specified stock threshold.
    """
    return await inventory_service.get_low_stock_items(
        db, threshold=threshold, store_id=store_id
    )


@router.get("/aggregate/{product_id}", response_model=AggregateStockResponse)
async def aggregate_product_stock(
    product_id: int,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get the total available stock for a product across all stores.
    """
    total = await inventory_service.get_total_available_stock(db, product_id=product_id)
    add_cache_headers(response, max_age=60)
    return {"product_id": product_id, "total_available_quantity": total}


@router.get("/debug/reserved", response_model=List[InventoryResponse])
async def debug_reserved_stock(
    store_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Diagnostic endpoint to identify items with active reservations.
    """
    from sqlalchemy import select
    from app.models.inventory import Inventory

    query = select(Inventory).filter(Inventory.reserved_quantity > 0)
    if store_id:
        query = query.filter(Inventory.store_id == store_id)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/snapshots", response_model=InventorySnapshotListResponse)
async def list_inventory_snapshots(
    db: AsyncSession = Depends(deps.get_db),
    store_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Retrieve historical inventory snapshots for timeline visualization.
    """
    from app.schemas.inventory import (
        InventorySnapshotListResponse,
        InventorySnapshotResponse,
    )

    items, total = await inventory_service.get_snapshots(
        db, store_id=store_id, skip=skip, limit=limit
    )

    # Manual mapping to include product name from joined relationship
    resp_items = []
    for item in items:
        resp_items.append(
            InventorySnapshotResponse(
                id=item.id,
                inventory_id=item.inventory_id,
                product_name=item.inventory.product.name,
                quantity=item.quantity,
                reserved_quantity=item.reserved_quantity,
                timestamp=item.timestamp,
                reason=item.reason,
            )
        )

    return {"items": resp_items, "total": total, "skip": skip, "limit": limit}
