#!/usr/bin/env python3
"""
WebSocket Connection Debugging
Tests WebSocket with detailed logging to identify HTTP 400 cause
"""

import asyncio
import time
import websockets
from urllib.parse import urlparse
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

    ws_url = settings.api.kalshi_ws_url
    parsed_path = urlparse(ws_url).path or "/"
    signing_paths = []
    if parsed_path not in ("", "/"):
        signing_paths.append(parsed_path)
    if settings.api.kalshi_ws_signing_path not in signing_paths:
        signing_paths.append(settings.api.kalshi_ws_signing_path)
    if "/" not in signing_paths:
        signing_paths.append("/")

    print(f"\n2. Authentication Details:")
    print(f"   Method: GET")
    print(f"   URL: {ws_url}")

    # Test 1: Dictionary headers (current implementation)
    print(f"\n3. TEST 1: Dictionary Headers (Kalshi Official Format)")

    last_timestamp = None
    last_signature = None
    for path in signing_paths:
        timestamp = str(int(time.time() * 1000))
        sign_message = f"{timestamp}GET{path}"
        signature = client._sign_request(timestamp, "GET", path)
        last_timestamp = timestamp
        last_signature = signature

        print(f"   Attempt Path: {path}")
        print(f"   Timestamp: {timestamp}")
        print(f"   Sign Message: {sign_message}")
        print(f"   Signature: {signature[:50]}... (length: {len(signature)})")

        headers_dict = {
            "KALSHI-ACCESS-KEY": client.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
            "X-API-KEY": client.api_key
        }

        print(f"   Headers: {list(headers_dict.keys())}")

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
                break

        except websockets.exceptions.InvalidStatusCode as e:
            print(f"   ❌ InvalidStatusCode: {e}")
            print(f"      Status: {e.status_code}")
            if hasattr(e, 'headers'):
                print(f"      Headers: {dict(e.headers)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"      Type: {type(e).__name__}")

    print(f"\n   Attempt: API-key-only headers")
    headers_dict = {
        "KALSHI-ACCESS-KEY": client.api_key,
        "Content-Type": "application/json",
        "X-API-KEY": client.api_key
    }
    try:
        print(f"   Connecting...")
        async with websockets.connect(
            ws_url,
            additional_headers=headers_dict,
            ping_interval=30,
            ping_timeout=10
        ) as websocket:
            print(f"   ✅ CONNECTED (api-key only)!")
            print(f"   WebSocket state: {websocket.state.name}")
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
    if last_timestamp is None:
        last_timestamp = str(int(time.time() * 1000))
    ts_int = int(last_timestamp)
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
    if last_signature is None:
        last_signature = client._sign_request(str(int(time.time() * 1000)), "GET", signing_paths[0])
    headers_list = [
        ("KALSHI-ACCESS-KEY", client.api_key),
        ("KALSHI-ACCESS-SIGNATURE", last_signature),
        ("KALSHI-ACCESS-TIMESTAMP", last_timestamp),
        ("Content-Type", "application/json"),
        ("X-API-KEY", client.api_key)
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
