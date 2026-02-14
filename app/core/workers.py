import asyncio
from datetime import datetime
from sqlalchemy import select, and_
from app.db.session import async_session_factory
from app.models.order import OrderItem, ReservationStatus, OrderStatus
from app.models.inventory import Inventory
from app.core.logging import logger


async def cleanup_expired_reservations():
    """
    Background worker to release stock from expired reservations.
    """
    logger.info("cleanup_worker_started")
    while True:
        try:
            async with async_session_factory() as db:
                # 1. Find expired active reservations
                now = datetime.utcnow()
                query = (
                    select(OrderItem)
                    .filter(
                        and_(
                            OrderItem.reservation_status == ReservationStatus.ACTIVE,
                            OrderItem.reservation_expires_at <= now,
                        )
                    )
                    .with_for_update()
                )

                result = await db.execute(query)
                expired_items = result.scalars().all()

                for item in expired_items:
                    # 2. Revert reserved stock in inventory
                    # We need the store_id from the Order
                    order_query = select(OrderItem.order_id).filter(
                        OrderItem.id == item.id
                    )
                    from app.models.order import Order

                    order_res = await db.execute(
                        select(Order).filter(Order.id == item.order_id)
                    )
                    order = order_res.scalar_one()

                    inventory_query = (
                        select(Inventory)
                        .filter(
                            and_(
                                Inventory.product_id == item.product_id,
                                Inventory.store_id == order.store_id,
                            )
                        )
                        .with_for_update()
                    )

                    inv_res = await db.execute(inventory_query)
                    inventory = inv_res.scalar_one_or_none()

                    if inventory:
                        inventory.reserved_quantity = max(
                            0, inventory.reserved_quantity - item.quantity
                        )
                        item.reservation_status = ReservationStatus.RELEASED

                        logger.info(
                            "reservation_released",
                            order_id=item.order_id,
                            product_id=item.product_id,
                            quantity=item.quantity,
                        )

                await db.commit()

        except Exception as e:
            logger.error("cleanup_worker_failed", error=str(e))
            await asyncio.sleep(10)  # Wait before retry

        await asyncio.sleep(60)  # Poll every minute


async def archive_old_failed_orders():
    """
    Retention policy: Delete failed orders older than 30 days.
    """
    from sqlalchemy import delete
    from app.models.order import FailedOrder
    from datetime import timedelta

    while True:
        try:
            async with async_session_factory() as db:
                retention_date = datetime.utcnow() - timedelta(days=30)
                query = delete(FailedOrder).filter(
                    FailedOrder.created_at <= retention_date
                )
                await db.execute(query)
                await db.commit()
                logger.info("dlq_cleanup_completed")
        except Exception as e:
            logger.error("dlq_cleanup_failed", error=str(e))

        await asyncio.sleep(86400)  # Run daily


def start_cleanup_worker():
    """
    Initializes the background tasks.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_expired_reservations())
    loop.create_task(archive_old_failed_orders())
