import asyncio
import httpx
import time
import uuid
import random
from typing import List, Dict

BASE_URL = "http://localhost:8001/api/v1"
CONCURRENT_REQUESTS = 50
TOTAL_REQUESTS = 200
STORE_ID = 1
PRODUCT_ID = 1
STOCK_QTY = 500
ITEMS_PER_ORDER = 3


async def check_app_ready(client: httpx.AsyncClient):
    """Wait for the application to be ready."""
    for _ in range(10):
        try:
            response = await client.get(f"{BASE_URL}/products/")
            if response.status_code == 200:
                print("Application is READY")
                return True
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


async def place_order(client: httpx.AsyncClient, session_id: int):
    """Place an order with a unique idempotency key."""
    idempotency_key = str(uuid.uuid4())
    payload = {
        "user_id": random.randint(1, 100),
        "store_id": STORE_ID,
        "items": [{"product_id": PRODUCT_ID, "quantity": ITEMS_PER_ORDER}],
        "idempotency_key": idempotency_key,
    }

    start_time = time.time()
    try:
        response = await client.post(f"{BASE_URL}/orders/", json=payload, timeout=10.0)
        latency = (time.time() - start_time) * 1000
        return {
            "status": response.status_code,
            "latency": latency,
            "success": response.status_code == 200,
            "error": (
                response.json().get("detail") if response.status_code != 200 else None
            ),
        }
    except Exception as e:
        return {
            "status": 500,
            "latency": (time.time() - start_time) * 1000,
            "success": False,
            "error": str(e),
        }


async def run_load_test():
    print(
        f"Starting Load Test: {TOTAL_REQUESTS} requests, {CONCURRENT_REQUESTS} concurrent"
    )
    print(
        f"Target: Store {STORE_ID}, Product {PRODUCT_ID}, Required Qty: {ITEMS_PER_ORDER}"
    )

    async with httpx.AsyncClient() as client:
        if not await check_app_ready(client):
            print("ERROR: Application not responding at http://localhost:8000")
            return

        # 1. Initialize Test Stock (Optional: assumes store/product exist or you seed them first)
        # We can't easily seed via API if there's no POST /inventory, let's assume seeded or
        # use a helper if we have DB access (but this script runs against API).

        tasks = []
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

        async def sem_task(i):
            async with semaphore:
                return await place_order(client, i)

        start_test = time.time()
        results = await asyncio.gather(*(sem_task(i) for i in range(TOTAL_REQUESTS)))
        end_test = time.time()

        # Statistics
        successes = [r for r in results if r["success"]]
        failures = [r for r in results if not r["success"]]
        latencies = [r["latency"] for r in results]

        print("\n" + "=" * 30)
        print("LOAD TEST RESULTS")
        print("=" * 30)
        print(f"Total Requests:      {len(results)}")
        print(f"Success Rate:        {len(successes) / len(results) * 100:.1f}%")
        print(f"Avg Latency:        {sum(latencies)/len(latencies):.2f}ms")
        print(f"Min Latency:        {min(latencies):.2f}ms")
        print(f"Max Latency:        {max(latencies):.2f}ms")
        print(f"Total Time:         {end_test - start_test:.2f}s")
        print("-" * 30)

        error_counts = {}
        for r in failures:
            err = str(r["error"])
            error_counts[err] = error_counts.get(err, 0) + 1

        for err, count in error_counts.items():
            print(f"Error [{err}]: {count} occurrences")

        # 2. Final Stock Integrity Check
        inv_res = await client.get(
            f"{BASE_URL}/inventory/check?product_id={PRODUCT_ID}&store_id={STORE_ID}"
        )
        if inv_res.status_code == 200:
            data = inv_res.json()
            print("-" * 30)
            print(f"Final Inventory State:")
            print(f"  Physical Quantity: {data['quantity']}")
            print(f"  Reserved Quantity: {data['reserved_quantity']}")
            print(f"  Available:         {data['available_quantity']}")

            # Validation logic
            expected_reserved = len(successes) * ITEMS_PER_ORDER
            print(f"  Expected Reserved: {expected_reserved}")
            if data["reserved_quantity"] == expected_reserved:
                print("SUCCESS: Inventory integrity verified.")
            else:
                print("FAILURE: Inventory mismatch detected!")


if __name__ == "__main__":
    asyncio.run(run_load_test())
