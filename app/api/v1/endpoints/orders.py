from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    StoreLoadMetrics,
)
from app.models.order import OrderStatus
from app.services.order_service import order_service

router = APIRouter()


@router.post("/", response_model=OrderResponse)
async def create_order(order_in: OrderCreate, db: AsyncSession = Depends(deps.get_db)):
    """
    Place a new order with inventory locking, latency tracking, and DLQ support.
    """
    return await order_service.create_order(db, order_in=order_in)


@router.get("/store/{store_id}/load", response_model=StoreLoadMetrics)
async def get_store_load(store_id: int, db: AsyncSession = Depends(deps.get_db)):
    """
    Get real-time load metrics for a specific store.
    """
    return await order_service.get_store_load(db, store_id=store_id)


@router.get("/", response_model=OrderListResponse)
async def read_orders(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="Filter by user"),
    store_id: Optional[int] = Query(None, description="Filter by store"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
):
    """
    Retrieve orders with pagination and multi-dimensional filtering.
    """
    orders, total = await order_service.get_orders(
        db, skip=skip, limit=limit, user_id=user_id, store_id=store_id, status=status
    )
    return {"items": orders, "total": total, "skip": skip, "limit": limit}


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(deps.get_db)):
    """
    Inspect a single order in detail, including reservation lifecycle status.
    """
    order = await order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
