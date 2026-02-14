import asyncio
import httpx
import uuid
import time
import random
from typing import List
from sqlalchemy import text
from app.db.session import async_session_factory

BASE_URL = "http://localhost:8001/api/v1"


async def run_idempotency_storm():
    print("\n--- TEST: Idempotency Storm ---")
    key = f"storm-{uuid.uuid4()}"
    payload = {
        "user_id": 1,
        "store_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
        "idempotency_key": key,
    }

    async with httpx.AsyncClient() as client:
        # Send 50 identical requests concurrently
        tasks = [client.post(f"{BASE_URL}/orders/", json=payload) for _ in range(50)]
        responses = await asyncio.gather(*tasks)

        status_codes = [r.status_code for r in responses]
        success_count = status_codes.count(200)

        print(f"Successes: {success_count} / 50")
        if (
            success_count == 50
        ):  # In FastAPI/SQLAlchemy, they might all return 200 due to idempotency hit logic
            # Check if only 1 item was actually reserved in DB
            inv_res = await client.get(
                f"{BASE_URL}/inventory/check?product_id=1&store_id=1"
            )
            reserved = inv_res.json()["reserved_quantity"]
            print(f"Total Reserved Quantity: {reserved}")
            # We assume it was 0 before this test if we run it alone or after a seed.
            # Let's seed first in the main.


async def run_dlq_stress():
    print("\n--- TEST: DLQ Stress ---")
    # Send an order with a non-existent user to trigger FK failure and push to DLQ
    payload = {
        "user_id": 9999,  # Invalid user
        "store_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
        "idempotency_key": str(uuid.uuid4()),
    }

    async with httpx.AsyncClient() as client:
        print("Sending invalid order (User ID 9999)...")
        res = await client.post(f"{BASE_URL}/orders/", json=payload)
        print(f"Order Response: {res.status_code}")

        # Verify it's in DLQ
        dlq_res = await client.get(f"{BASE_URL}/dlq/")
        dlq_data = dlq_res.json()
        print(f"DLQ Total Count: {dlq_data['total']}")

        matching = [item for item in dlq_data["items"] if item["user_id"] == 9999]
        if matching:
            print(
                f"SUCCESS: Invalid order found in DLQ with error: {matching[0]['error_message'][:50]}..."
            )
        else:
            print("FAILURE: Invalid order NOT found in DLQ.")


async def run_store_load_validation():
    print("\n--- TEST: Store Load Metrics Validation ---")
    async with httpx.AsyncClient() as client:
        # 1. Get initial load
        initial = await client.get(f"{BASE_URL}/orders/store/1/load")
        print(f"Initial Load Score: {initial.json()['total_load_score']}")

        # 2. Burst of 20 orders
        print("Spiking 20 orders...")
        tasks = []
        for i in range(20):
            payload = {
                "user_id": random.randint(1, 100),
                "store_id": 1,
                "items": [{"product_id": 1, "quantity": 1}],
                "idempotency_key": str(uuid.uuid4()),
            }
            tasks.append(client.post(f"{BASE_URL}/orders/", json=payload))
        await asyncio.gather(*tasks)

        # 3. Check load again
        final = await client.get(f"{BASE_URL}/orders/store/1/load")
        data = final.json()
        print(f"Final Load Score: {data['total_load_score']}")
        print(f"Pending Count: {data['pending_orders_count']}")
        print(f"Velocity (per min): {data['recent_velocity_per_min']}")

        if data["pending_orders_count"] >= 20:
            print("SUCCESS: Store load metrics accurately reflected the burst.")


async def run_reservation_expiry_test():
    print("\n--- TEST: Reservation Expiry ---")
    # 1. Place an order to reserve stock
    async with httpx.AsyncClient() as client:
        payload = {
            "user_id": 1,
            "store_id": 1,
            "items": [{"product_id": 1, "quantity": 5}],
            "idempotency_key": str(uuid.uuid4()),
        }
        await client.post(f"{BASE_URL}/orders/", json=payload)

        # Check reserved qty
        inv_before = await client.get(
            f"{BASE_URL}/inventory/check?product_id=1&store_id=1"
        )
        reserved_before = inv_before.json()["reserved_quantity"]
        print(f"Reserved before expiry: {reserved_before}")

        # 2. Manually "expire" the reservation in DB
        print("Manipulating DB to expire reservation...")
        async with async_session_factory() as db:
            await db.execute(
                text(
                    "UPDATE order_items SET reservation_expires_at = reservation_expires_at - interval '30 minutes'"
                )
            )
            await db.commit()

        print("Waiting 65 seconds for background cleanup worker...")
        await asyncio.sleep(65)

        # 3. Check if reserved qty is released
        inv_after = await client.get(
            f"{BASE_URL}/inventory/check?product_id=1&store_id=1"
        )
        reserved_after = inv_after.json()["reserved_quantity"]
        print(f"Reserved after expiry: {reserved_after}")

        if reserved_after < reserved_before:
            print("SUCCESS: Reservation cleanup worker released expired stock.")
        else:
            print("FAILURE: Stock not released.")


async def run_long_running_load_test():
    print("\n--- TEST: Long-Running Load Test ---")
    print("Sending 100 orders in batches of 10...")
    async with httpx.AsyncClient() as client:
        for batch in range(10):
            print(f"Batch {batch+1}/10...")
            tasks = []
            for i in range(10):
                payload = {
                    "user_id": random.randint(1, 100),
                    "store_id": 1,
                    "items": [{"product_id": 1, "quantity": 1}],
                    "idempotency_key": str(uuid.uuid4()),
                }
                tasks.append(client.post(f"{BASE_URL}/orders/", json=payload))
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)  # Small delay between batches
    print("Long-running load test completed.")


async def main():
    print("Assuming database is already seeded/clean.")
    await run_idempotency_storm()
    await run_dlq_stress()
    await run_store_load_validation()
    await run_long_running_load_test()
    await run_reservation_expiry_test()


if __name__ == "__main__":
    asyncio.run(main())
