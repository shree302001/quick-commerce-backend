import asyncio
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.user import User, UserRole
from app.models.store import Store
from app.models.product import Product, Category
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, FailedOrder


async def seed():
    async with async_session_factory() as db:
        print("Cleaning up existing test data...")
        # Clear tables (Order first due to FK)
        from sqlalchemy import text

        await db.execute(
            text(
                "TRUNCATE order_items, orders, failed_orders, inventory, products, stores, categories, users RESTART IDENTITY CASCADE"
            )
        )

        print("Seeding test data...")
        # 0. Users
        for i in range(1, 101):
            user = User(
                email=f"user{i}@example.com",
                hashed_password="hashed_password",
                full_name=f"Test User {i}",
                role=UserRole.CUSTOMER,
                is_active=True,
            )
            db.add(user)
        await db.flush()

        # 1. Category
        cat = Category(name="Electronics")
        db.add(cat)
        await db.flush()

        # 2. Store
        store = Store(
            name="Test Store Alpha",
            location="123 Admin Lane",
            latitude=0.0,
            longitude=0.0,
        )
        db.add(store)
        await db.flush()

        # 3. Product
        product = Product(
            name="Power Bank", sku="PB-001", price=1200.0, category_id=cat.id
        )
        db.add(product)
        await db.flush()

        # 4. Inventory
        inventory = Inventory(
            product_id=product.id,
            store_id=store.id,
            quantity=500,  # This matches STOCK_QTY in load_test.py
            reserved_quantity=0,
        )
        db.add(inventory)

        await db.commit()
        print(
            f"Seeded: Store ID={store.id}, Product ID={product.id}, Qty={inventory.quantity}"
        )


if __name__ == "__main__":
    asyncio.run(seed())
