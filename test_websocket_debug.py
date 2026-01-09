#!/usr/bin/env python3
"""
WebSocket Connection Debugging
Tests WebSocket with detailed logging to identify HTTP 400 cause
"""

import asyncio
import time
import websockets
from pathlib import Path
from src.clients.kalshi_client import KalshiClient
from src.config.settings import settings

async def test_websocket_detailed():
    print("="*70)
    print("  WEBSOCKET CONNECTION DEBUGGING")
    print("="*70)

    # Initialize Kalshi client
    client = KalshiClient()
    client._load_private_key()

    print(f"\n1. Configuration:")
    print(f"   API Key: {client.api_key[:15]}...")
    print(f"   Base URL: {client.base_url}")
    print(f"   Private Key: Loaded ✅")

    # Generate authentication
    timestamp = str(int(time.time() * 1000))
    path = "/trade-api/ws/v2"
    method = "GET"

    print(f"\n2. Authentication Details:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Method: {method}")
    print(f"   Path: {path}")

    # Create signing message
    sign_message = f"{timestamp}{method}{path}"
    print(f"   Sign Message: {sign_message}")

    # Generate signature
    signature = client._sign_request(timestamp, method, path)
    print(f"   Signature: {signature[:50]}... (length: {len(signature)})")

    # Test 1: Dictionary headers (current implementation)
    print(f"\n3. TEST 1: Dictionary Headers (Kalshi Official Format)")
    headers_dict = {
        "KALSHI-ACCESS-KEY": client.api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    print(f"   Headers: {list(headers_dict.keys())}")

    ws_url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    print(f"   URL: {ws_url}")

    try:
        print(f"   Connecting...")
        async with websockets.connect(
            ws_url,
            additional_headers=headers_dict,
            ping_interval=30,
            ping_timeout=10
        ) as websocket:
            print(f"   ✅ CONNECTED!")
            print(f"   WebSocket state: {websocket.state.name}")

            # Try to receive initial message
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"   Received message: {msg}")
            except asyncio.TimeoutError:
                print(f"   No immediate message (normal)")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"   ❌ InvalidStatusCode: {e}")
        print(f"      Status: {e.status_code}")
        if hasattr(e, 'headers'):
            print(f"      Headers: {dict(e.headers)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"      Type: {type(e).__name__}")

    # Test 2: Check REST API with same credentials (should work)
    print(f"\n4. TEST 2: Verify REST API Works (Baseline)")
    try:
        balance = await client.get_balance()
        print(f"   ✅ REST API works: Balance ${balance.get('balance', 0) / 100:.2f}")
    except Exception as e:
        print(f"   ❌ REST API failed: {e}")

    # Test 3: Check timestamp freshness
    print(f"\n5. TEST 3: Timestamp Validation")
    import datetime
    ts_int = int(timestamp)
    ts_dt = datetime.datetime.fromtimestamp(ts_int / 1000.0)
    now = datetime.datetime.now()
    diff = (now - ts_dt).total_seconds()
    print(f"   Timestamp: {ts_dt}")
    print(f"   Now: {now}")
    print(f"   Difference: {diff:.2f} seconds")
    if abs(diff) > 60:
        print(f"   ⚠️ WARNING: Time difference > 60 seconds!")
    else:
        print(f"   ✅ Timestamp is fresh")

    # Test 4: Alternative header format
    print(f"\n6. TEST 4: Try List of Tuples Format")
    headers_list = [
        ("KALSHI-ACCESS-KEY", client.api_key),
        ("KALSHI-ACCESS-SIGNATURE", signature),
        ("KALSHI-ACCESS-TIMESTAMP", timestamp)
    ]

    try:
        print(f"   Connecting with list format...")
        async with websockets.connect(
            ws_url,
            additional_headers=headers_list,
            ping_interval=30,
            ping_timeout=10
        ) as websocket:
            print(f"   ✅ CONNECTED WITH LIST FORMAT!")
    except Exception as e:
        print(f"   ❌ List format also failed: {type(e).__name__}")

    # Test 5: Check without headers (expect 401)
    print(f"\n7. TEST 5: No Auth Headers (Expect 401/403)")
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"   ❌ Connected without auth (unexpected!)")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"   ✅ Rejected as expected: {e.status_code}")
    except Exception as e:
        print(f"   Response: {type(e).__name__}")

    await client.close()

    print(f"\n" + "="*70)
    print("  DEBUGGING COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_websocket_detailed())
