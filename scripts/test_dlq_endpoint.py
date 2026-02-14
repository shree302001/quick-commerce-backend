import httpx
import json


async def test():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:8001/api/v1/dlq/")
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
        try:
            print(f"JSON: {json.dumps(r.json(), indent=2)}")
        except:
            print(f"Content: {r.text}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
