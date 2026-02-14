import time
import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.order_repo import order_repo
from app.repositories.product_repo import product_repo
from app.services.inventory_service import inventory_service
from app.schemas.order import OrderCreate
from app.models.order import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    FailedOrder,
)
from app.core.logging import logger


class OrderService:
    async def create_order(self, db: AsyncSession, order_in: OrderCreate) -> Order:
        start_time = time.time()

        # 1. Idempotency Check
        existing_order = await order_repo.get_by_idempotency_key(
            db, idempotency_key=order_in.idempotency_key
        )
        if existing_order:
            logger.info(
                "idempotency_hit",
                idempotency_key=order_in.idempotency_key,
                order_id=existing_order.id,
            )
            return existing_order

        # 2. Reserve Inventory and calculate total
        try:
            total_amount = 0.0
            order_items_to_create = []
            # Default reservation expiry: 15 minutes
            expiry_time = datetime.utcnow() + timedelta(minutes=15)

            for item in order_in.items:
                # Fetch product for price
                product = await product_repo.get(db, id=item.product_id)
                if not product:
                    raise ValueError(f"Product {item.product_id} not found")

                # Reserve stock (this now uses FOR UPDATE locking)
                await inventory_service.reserve_stock(
                    db,
                    product_id=item.product_id,
                    store_id=order_in.store_id,
                    quantity=item.quantity,
                )

                # Prepare OrderItem
                db_item = OrderItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_order=product.price,
                    reservation_expires_at=expiry_time,
                )
                order_items_to_create.append(db_item)
                total_amount += product.price * item.quantity

            # 3. Create Order
            checkout_latency = (time.time() - start_time) * 1000

            db_order = Order(
                user_id=order_in.user_id,
                store_id=order_in.store_id,
                total_amount=total_amount,
                idempotency_key=order_in.idempotency_key,
                status=OrderStatus.PENDING,
                items=order_items_to_create,
                checkout_latency_ms=round(checkout_latency, 2),
            )

            # Record initial timeline entry
            db_order.timeline.append(
                OrderStatusHistory(status=OrderStatus.PENDING, notes="Order created")
            )

            db.add(db_order)
            await db.commit()
            await db.refresh(db_order)
            return db_order

        except Exception as e:
            await db.rollback()
            # Push to DLQ: FailedOrder
            failed_order = FailedOrder(
                user_id=order_in.user_id,
                store_id=order_in.store_id,
                payload=json.dumps(order_in.model_dump(), default=str),
                error_message=str(e),
                idempotency_key=order_in.idempotency_key,
            )
            db.add(failed_order)
            await db.commit()

            logger.error(
                "order_creation_failed_pushed_to_dlq",
                error=str(e),
                idempotency_key=order_in.idempotency_key,
                user_id=order_in.user_id,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create order. Recorded in DLQ. Error: {str(e)}",
            )

        return db_order

    async def get_orders(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        store_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
    ) -> Tuple[List[Order], int]:
        return await order_repo.get_multi_with_filters(
            db,
            skip=skip,
            limit=limit,
            user_id=user_id,
            store_id=store_id,
            status=status,
        )

    async def get_order(self, db: AsyncSession, order_id: int) -> Optional[Order]:
        return await order_repo.get(db, id=order_id)

    async def get_store_load(self, db: AsyncSession, store_id: int) -> dict:
        return await order_repo.get_store_load_metrics(db, store_id=store_id)

    async def replay_failed_order(
        self, db: AsyncSession, failed_order_id: int
    ) -> Order:
        """
        Retry a failed order from the DLQ.
        """
        failed_order = await db.get(FailedOrder, failed_order_id)
        if not failed_order:
            raise HTTPException(status_code=404, detail="Failed order not found")

        # Parse payload back to OrderCreate
        order_data = json.loads(failed_order.payload)
        order_in = OrderCreate(**order_data)

        # Attempt to create order again
        try:
            # We bypass the idempotency check internal to create_order by calling logic directly
            # or just call create_order and handle the idempotency hit if it somehow exists
            # But here we want a fresh attempt.
            new_order = await self.create_order(db, order_in=order_in)

            # If successful, mark failed order as resolved
            failed_order.status = "resolved"
            failed_order.retry_count += 1
            await db.commit()
            return new_order
        except Exception as e:
            failed_order.retry_count += 1
            failed_order.error_message = f"Retry failed: {str(e)}"
            await db.commit()
            raise HTTPException(
                status_code=500, detail=f"Replay failed again: {str(e)}"
            )

    async def list_failed_orders(
        self, db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> Tuple[List[FailedOrder], int]:
        query = select(FailedOrder).offset(skip).limit(limit)
        count_query = select(func.count()).select_from(FailedOrder)

        result = await db.execute(query)
        total = (await db.execute(count_query)).scalar_one()
        return list(result.scalars().all()), total


order_service = OrderService()
