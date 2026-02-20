
import httpx
import asyncio

async def test_invalid_uuid():
    url = "http://localhost:8000/sakhi/chat"
    payload = {
        "user_id": "test_user",  # Previously caused 500
        "message": "hello",
        "language": "en"
    }
    async with httpx.AsyncClient() as client:
        print(f"Testing {url} with invalid UUID 'test_user'...")
        resp = await client.post(url, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")

if __name__ == "__main__":
    asyncio.run(test_invalid_uuid())
