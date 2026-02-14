from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.order import OrderResponse
from app.schemas.base import BaseSchema
from app.services.order_service import order_service

router = APIRouter()


class FailedOrderResponse(BaseSchema):
    id: int
    user_id: int
    store_id: int
    error_message: str
    retry_count: int
    status: str
    created_at: str


class FailedOrderListResponse(BaseSchema):
    items: List[FailedOrderResponse]
    total: int


@router.get("/", response_model=FailedOrderListResponse)
async def list_dlq(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List failed orders in the Dead Letter Queue.
    """
    items, total = await order_service.list_failed_orders(db, skip=skip, limit=limit)
    # Convert created_at to string for simplicity in this schema
    resp_items = []
    for item in items:
        resp_items.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "store_id": item.store_id,
                "error_message": item.error_message,
                "retry_count": item.retry_count,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
            }
        )
    return {"items": resp_items, "total": total}


@router.post("/{failed_order_id}/replay", response_model=OrderResponse)
async def replay_failed_order(
    failed_order_id: int, db: AsyncSession = Depends(deps.get_db)
):
    """
    Attempt to replay a failed order.
    """
    return await order_service.replay_failed_order(db, failed_order_id=failed_order_id)
