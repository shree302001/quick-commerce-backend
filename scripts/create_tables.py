import asyncio
from app.db.base import Base
from app.db.session import engine

# Import all models to ensure they are registered with Base
from app.models.user import User
from app.models.store import Store
from app.models.product import Product, Category
from app.models.inventory import Inventory, InventorySnapshot
from app.models.order import Order, OrderItem, OrderStatusHistory, FailedOrder


async def create_tables():
    async with engine.begin() as conn:
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_tables())
