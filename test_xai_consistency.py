#!/usr/bin/env python3
"""Test xAI/Grok API consistency"""

import asyncio
import httpx
import ssl
from src.config.settings import settings

async def test_xai():
    ssl_context = ssl.create_default_context()
    async with httpx.AsyncClient(timeout=10.0, verify=ssl_context, http2=False) as client:
        response = await client.get(
            'https://api.x.ai/v1/models',
            headers={'Authorization': f'Bearer {settings.api.xai_api_key}'}
        )
        if response.status_code == 200:
            models = response.json().get('data', [])
            return True, len(models)
        else:
            return False, response.status_code

async def main():
    print("Testing xAI/Grok API 5 times...\n")
    results = []

    for i in range(5):
        try:
            success, data = await test_xai()
            if success:
                print(f"Test {i+1}/5: ✅ Working - {data} models")
                results.append(True)
            else:
                print(f"Test {i+1}/5: ❌ Failed - Status {data}")
                results.append(False)
        except Exception as e:
            print(f"Test {i+1}/5: ❌ Error - {e}")
            results.append(False)

        if i < 4:
            await asyncio.sleep(1)

    print(f"\n{'='*50}")
    print(f"Results: {sum(results)}/5 successful ({sum(results)/5*100:.0f}%)")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
