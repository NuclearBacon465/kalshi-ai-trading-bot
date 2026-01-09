#!/usr/bin/env python3
"""
Deep WebSocket Debugging - Try Multiple Authentication Methods
"""

import asyncio
import time
import websockets
import json
from src.clients.kalshi_client import KalshiClient

async def test_websocket_approaches():
    print("="*70)
    print("  DEEP WEBSOCKET DEBUGGING - TRYING ALL METHODS")
    print("="*70)

    client = KalshiClient()
    client._load_private_key()

    ws_url = "wss://api.elections.kalshi.com/trade-api/ws/v2"

    # APPROACH 1: Current method (dictionary headers)
    print("\n🔍 APPROACH 1: Dictionary Headers (Current)")
    timestamp = str(int(time.time() * 1000))
    signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

    headers_dict = {
        "KALSHI-ACCESS-KEY": client.api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    print(f"   Timestamp: {timestamp}")
    print(f"   API Key: {client.api_key[:15]}...")
    print(f"   Signature: {signature[:50]}...")

    try:
        async with websockets.connect(ws_url, additional_headers=headers_dict) as ws:
            print(f"   ✅ CONNECTED!")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # APPROACH 2: Try with different path signature
    print("\n🔍 APPROACH 2: Different Path in Signature")
    timestamp = str(int(time.time() * 1000))

    # Try just /ws/v2
    signature = client._sign_request(timestamp, "GET", "/ws/v2")
    headers_dict = {
        "KALSHI-ACCESS-KEY": client.api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    try:
        async with websockets.connect(ws_url, additional_headers=headers_dict) as ws:
            print(f"   ✅ CONNECTED with /ws/v2!")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # APPROACH 3: Connect first, then authenticate via message
    print("\n🔍 APPROACH 3: Connect Then Authenticate via Message")
    try:
        async with websockets.connect(ws_url) as ws:
            print(f"   Connected to WebSocket...")

            timestamp = str(int(time.time() * 1000))
            signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

            auth_msg = {
                "type": "authenticate",
                "key": client.api_key,
                "signature": signature,
                "timestamp": timestamp
            }

            await ws.send(json.dumps(auth_msg))
            print(f"   Sent auth message...")

            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"   ✅ Response: {response}")
            return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # APPROACH 4: Try with query parameters
    print("\n🔍 APPROACH 4: URL Query Parameters")
    timestamp = str(int(time.time() * 1000))
    signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

    url_with_params = f"{ws_url}?key={client.api_key}&signature={signature}&timestamp={timestamp}"

    try:
        async with websockets.connect(url_with_params) as ws:
            print(f"   ✅ CONNECTED with query params!")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # APPROACH 5: Check if we need lowercase headers
    print("\n🔍 APPROACH 5: Lowercase Header Names")
    timestamp = str(int(time.time() * 1000))
    signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

    headers_lower = {
        "kalshi-access-key": client.api_key,
        "kalshi-access-signature": signature,
        "kalshi-access-timestamp": timestamp
    }

    try:
        async with websockets.connect(ws_url, additional_headers=headers_lower) as ws:
            print(f"   ✅ CONNECTED with lowercase headers!")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # APPROACH 6: Try demo API to see if it's an account permission issue
    print("\n🔍 APPROACH 6: Try Demo API")
    demo_url = "wss://demo-api.kalshi.co/trade-api/ws/v2"
    timestamp = str(int(time.time() * 1000))
    signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

    headers_dict = {
        "KALSHI-ACCESS-KEY": client.api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    try:
        async with websockets.connect(demo_url, additional_headers=headers_dict) as ws:
            print(f"   ✅ CONNECTED to DEMO API!")
            print(f"   This means your code is correct but production API needs permission")
            return True
    except Exception as e:
        print(f"   ❌ Demo also failed: {e}")

    # APPROACH 7: Try with Authorization header (REST-style)
    print("\n🔍 APPROACH 7: Authorization Header (REST-style)")
    timestamp = str(int(time.time() * 1000))
    signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

    headers_auth = {
        "Authorization": f"Bearer {client.api_key}",
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    try:
        async with websockets.connect(ws_url, additional_headers=headers_auth) as ws:
            print(f"   ✅ CONNECTED with Authorization header!")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # APPROACH 8: Check server response details
    print("\n🔍 APPROACH 8: Detailed Error Analysis")
    timestamp = str(int(time.time() * 1000))
    signature = client._sign_request(timestamp, "GET", "/trade-api/ws/v2")

    headers_dict = {
        "KALSHI-ACCESS-KEY": client.api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    try:
        async with websockets.connect(ws_url, additional_headers=headers_dict) as ws:
            print(f"   ✅ CONNECTED!")
            return True
    except websockets.exceptions.InvalidStatus as e:
        print(f"   ❌ InvalidStatus Error:")
        print(f"      Status Code: {e.response.status_code}")
        print(f"      Response Headers: {dict(e.response.headers)}")
        print(f"      Response Body: {e.response.body if hasattr(e.response, 'body') else 'N/A'}")
    except Exception as e:
        print(f"   ❌ Other error: {type(e).__name__}: {e}")

    await client.close()

    print("\n" + "="*70)
    print("  ALL APPROACHES FAILED - LIKELY ACCOUNT PERMISSION ISSUE")
    print("="*70)
    return False

if __name__ == "__main__":
    asyncio.run(test_websocket_approaches())
