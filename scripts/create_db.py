import asyncio
import asyncpg
from app.core.config import settings


async def create_db():
    # Parse the current URL to connect to the 'postgres' default database
    # format: postgresql+asyncpg://user:pass@host/dbname
    url = settings.DATABASE_URL.replace("quick_commerce", "postgres").replace(
        "postgresql+asyncpg://", "postgresql://"
    )

    try:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute("CREATE DATABASE quick_commerce")
            print("Database 'quick_commerce' created successfully.")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print("Database 'quick_commerce' already exists.")
        finally:
            await conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == "__main__":
    asyncio.run(create_db())
