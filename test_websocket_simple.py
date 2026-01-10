#!/usr/bin/env python3
"""
Simple WebSocket test - no timeout parameter issues.
"""

import asyncio
import websockets
import time
import base64
import json
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Load private key
def load_private_key():
    with open("kalshi_private_key", 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def sign_request(private_key, timestamp: str, method: str, path: str) -> str:
    """Sign request using RSA PSS."""
    message = timestamp + method.upper() + path
    message_bytes = message.encode('utf-8')

    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode('utf-8')


async def test_websocket_with_auth():
    """Test WebSocket with proper auth."""
    print("="*70)
    print("WEBSOCKET CONNECTION TEST")
    print("="*70)

    api_key = "c3f8ac74-8747-4638-aa7b-c97f0b2e777a"
    private_key = load_private_key()

    timestamp = str(int(time.time() * 1000))
    signature = sign_request(private_key, timestamp, "GET", "/trade-api/ws/v2")

    headers = {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    print(f"\nAuth Details:")
    print(f"  Timestamp: {timestamp}")
    print(f"  API Key: {api_key}")
    print(f"  Signature (length): {len(signature)} chars")
    print(f"  Message signed: {timestamp}GET/trade-api/ws/v2")

    url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    print(f"\nConnecting to: {url}")

    try:
        async with websockets.connect(url, extra_headers=headers) as websocket:
            print("\n✅ CONNECTION SUCCESSFUL!")
            print("="*70)

            # Try to subscribe
            subscribe_msg = {
                "cmd": "subscribe",
                "params": {
                    "channels": ["ticker"]
                }
            }

            print(f"\n📤 Sending subscribe command...")
            await websocket.send(json.dumps(subscribe_msg))
            print(f"   {json.dumps(subscribe_msg, indent=2)}")

            # Wait for response
            print("\n⏳ Waiting for response (10 seconds)...")
            try:
                response = await asyncio.wait_for(websocket.recv(), 10.0)
                print(f"\n📨 RECEIVED:")
                try:
                    response_json = json.loads(response)
                    print(json.dumps(response_json, indent=2))
                except:
                    print(response)
            except asyncio.TimeoutError:
                print("\n⏰ No response within 10 seconds")
                print("   (This might be normal - need to subscribe to specific tickers)")

            print("\n✅ WebSocket is WORKING!")

    except Exception as e:
        print(f"\n❌ CONNECTION FAILED")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {e}")

        # Extract status code if available
        if hasattr(e, 'status_code'):
            print(f"   HTTP Status: {e.status_code}")

        # Extract headers if available
        if hasattr(e, 'headers'):
            print(f"\n   Response Headers:")
            for k, v in e.headers.items():
                print(f"      {k}: {v}")

        print("\n" + "="*70)
        print("DIAGNOSIS:")
        print("="*70)

        error_str = str(e)
        if "400" in error_str or (hasattr(e, 'status_code') and e.status_code == 400):
            print("HTTP 400 = Bad Request")
            print("\nPossible causes:")
            print("1. API key lacks WebSocket permissions (MOST LIKELY)")
            print("2. Invalid authentication format")
            print("3. Rate limiting")
            print("\nTo enable WebSocket:")
            print("  Email: support@kalshi.com")
            print("  Subject: Enable WebSocket Access")
            print(f"  API Key: {api_key}")
        elif "401" in error_str:
            print("HTTP 401 = Unauthorized")
            print("Authentication credentials are invalid")
        elif "403" in error_str:
            print("HTTP 403 = Forbidden")
            print("API key doesn't have permission for WebSocket")


async def test_rest_api_comparison():
    """Compare with REST API to prove auth works."""
    print("\n" + "="*70)
    print("REST API COMPARISON (Control Test)")
    print("="*70)

    import httpx

    api_key = "c3f8ac74-8747-4638-aa7b-c97f0b2e777a"
    private_key = load_private_key()

    timestamp = str(int(time.time() * 1000))
    path = "/trade-api/v2/portfolio/balance"
    signature = sign_request(private_key, timestamp, "GET", path)

    headers = {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.elections.kalshi.com{path}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                balance = data.get('balance', 0) / 100
                print(f"✅ REST API WORKS: Balance ${balance:.2f}")
                print("\nThis proves:")
                print("  ✅ API key is valid")
                print("  ✅ Private key is correct")
                print("  ✅ Signature method works")
                print("  ✅ Authentication credentials are good")
                print("\nSo if WebSocket fails, it's a permissions issue.")
            else:
                print(f"❌ REST API failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ REST API error: {e}")


async def main():
    # First prove REST works
    await test_rest_api_comparison()

    # Then test WebSocket
    await test_websocket_with_auth()


if __name__ == "__main__":
    asyncio.run(main())
