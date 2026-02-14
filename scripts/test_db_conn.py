import asyncio
from sqlalchemy import text
from app.db.session import engine


async def test_conn():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("Database connection SUCCESSFUL")
    except Exception as e:
        print(f"Database connection FAILED: {e}")
        print("\nPlease check DATABASE_URL in app/core/config.py or .env file.")


if __name__ == "__main__":
    asyncio.run(test_conn())
