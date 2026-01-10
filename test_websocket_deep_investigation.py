#!/usr/bin/env python3
"""
DEEP WebSocket Investigation - Multiple Approaches

Tests:
1. Raw WebSocket connection (no auth)
2. WebSocket with auth headers
3. Different WebSocket libraries
4. Check CloudFront headers in detail
5. Try official Kalshi SDK WebSocket if available
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


async def test_1_raw_websocket():
    """Test 1: Raw WebSocket connection without auth."""
    print("\n" + "="*70)
    print("TEST 1: Raw WebSocket Connection (No Auth)")
    print("="*70)
    print("URL: wss://api.elections.kalshi.com/trade-api/ws/v2")
    print("Expected: Should connect but may get auth error message")

    try:
        async with websockets.connect(
            "wss://api.elections.kalshi.com/trade-api/ws/v2",
            timeout=10
        ) as websocket:
            print("✅ CONNECTED! WebSocket endpoint is reachable")

            # Try to receive a message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received: {message}")
            except asyncio.TimeoutError:
                print("⏰ No message received (timeout)")

            # Try to send a subscribe command
            print("\nSending subscribe command...")
            subscribe_msg = {
                "cmd": "subscribe",
                "params": {
                    "channels": ["ticker"]
                }
            }
            await websocket.send(json.dumps(subscribe_msg))

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection rejected: HTTP {e.status_code}")
        print(f"   Headers: {e.headers}")
        print(f"   Body: {e.response_body if hasattr(e, 'response_body') else 'N/A'}")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")


async def test_2_with_auth():
    """Test 2: WebSocket with authentication."""
    print("\n" + "="*70)
    print("TEST 2: WebSocket with Authentication")
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

    print(f"Auth Headers:")
    print(f"  Timestamp: {timestamp}")
    print(f"  API Key: {api_key[:20]}...")
    print(f"  Signature (first 50): {signature[:50]}...")

    try:
        async with websockets.connect(
            "wss://api.elections.kalshi.com/trade-api/ws/v2",
            additional_headers=headers,
            timeout=10
        ) as websocket:
            print("✅ CONNECTED with auth!")

            # Send subscribe
            subscribe_msg = {
                "cmd": "subscribe",
                "params": {
                    "channels": ["ticker"]
                }
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"📤 Sent: {json.dumps(subscribe_msg)}")

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response within 5 seconds")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection rejected: HTTP {e.status_code}")
        print(f"\n🔍 Response Headers:")
        for key, value in e.headers.items():
            print(f"   {key}: {value}")

        # Check if it's CloudFront
        if 'server' in e.headers or 'Server' in e.headers:
            server = e.headers.get('server') or e.headers.get('Server')
            print(f"\n🌐 Server: {server}")
            if 'CloudFront' in server:
                print("   ⚠️ Request blocked by CloudFront (AWS CDN)")
                print("   This means request didn't reach Kalshi's servers")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


async def test_3_different_urls():
    """Test 3: Try different WebSocket URL variations."""
    print("\n" + "="*70)
    print("TEST 3: Different URL Variations")
    print("="*70)

    api_key = "c3f8ac74-8747-4638-aa7b-c97f0b2e777a"
    private_key = load_private_key()

    urls = [
        ("wss://api.elections.kalshi.com/trade-api/ws/v2", "/trade-api/ws/v2"),
        ("wss://api.elections.kalshi.com/ws/v2", "/ws/v2"),
        ("wss://api.elections.kalshi.com/trade-api/ws", "/trade-api/ws"),
        ("wss://trading-api.kalshi.com/trade-api/ws/v2", "/trade-api/ws/v2"),
    ]

    for url, sign_path in urls:
        print(f"\n🔗 Trying: {url}")
        print(f"   Sign path: {sign_path}")

        timestamp = str(int(time.time() * 1000))
        signature = sign_request(private_key, timestamp, "GET", sign_path)

        headers = {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp
        }

        try:
            async with websockets.connect(url, additional_headers=headers, timeout=5) as ws:
                print(f"   ✅ CONNECTED!")
                return
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"   ❌ HTTP {e.status_code}")
        except Exception as e:
            print(f"   ❌ {type(e).__name__}: {str(e)[:50]}")


async def test_4_check_rest_api():
    """Test 4: Verify REST API works with same credentials."""
    print("\n" + "="*70)
    print("TEST 4: REST API Verification (Control Test)")
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.elections.kalshi.com{path}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                balance = data.get('balance', 0) / 100
                print(f"✅ REST API WORKS: Balance ${balance:.2f}")
                print("   Auth credentials are VALID")
                print("   Private key is CORRECT")
                print("   API key has REST permissions")
            else:
                print(f"❌ REST API failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ REST API error: {e}")


async def test_5_ws_protocol_inspection():
    """Test 5: Inspect WebSocket handshake in detail."""
    print("\n" + "="*70)
    print("TEST 5: WebSocket Protocol Inspection")
    print("="*70)

    import ssl

    api_key = "c3f8ac74-8747-4638-aa7b-c97f0b2e777a"
    private_key = load_private_key()

    timestamp = str(int(time.time() * 1000))
    signature = sign_request(private_key, timestamp, "GET", "/trade-api/ws/v2")

    # Try with custom SSL context
    ssl_context = ssl.create_default_context()

    headers = {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

    print("Headers being sent:")
    for k, v in headers.items():
        if k == "KALSHI-ACCESS-SIGNATURE":
            print(f"  {k}: {v[:50]}... (length: {len(v)})")
        else:
            print(f"  {k}: {v}")

    try:
        # Enable extra debugging
        import logging
        logging.basicConfig(level=logging.DEBUG)

        async with websockets.connect(
            "wss://api.elections.kalshi.com/trade-api/ws/v2",
            additional_headers=headers,
            ssl=ssl_context,
            timeout=10
        ) as ws:
            print("✅ CONNECTED!")
    except Exception as e:
        print(f"❌ Failed: {e}")

        # Check if error has response details
        if hasattr(e, 'headers'):
            print("\n🔍 Error response headers:")
            for k, v in e.headers.items():
                print(f"   {k}: {v}")


async def main():
    """Run all tests."""
    print("="*70)
    print("KALSHI WEBSOCKET DEEP INVESTIGATION")
    print("="*70)
    print("\nThis will test WebSocket connectivity using multiple approaches")
    print("to identify the exact cause of the HTTP 400 error.")

    # Test 1: Raw connection
    await test_1_raw_websocket()

    # Test 2: With auth
    await test_2_with_auth()

    # Test 3: Different URLs
    await test_3_different_urls()

    # Test 4: REST API control
    await test_4_check_rest_api()

    # Test 5: Protocol inspection
    await test_5_ws_protocol_inspection()

    print("\n" + "="*70)
    print("INVESTIGATION COMPLETE")
    print("="*70)
    print("\n📋 ANALYSIS:")
    print("If ALL WebSocket tests fail with HTTP 400 but REST works:")
    print("  → API key lacks WebSocket permissions")
    print("\nIf some URLs work:")
    print("  → Wrong WebSocket URL or path")
    print("\nIf raw connection works but auth fails:")
    print("  → Authentication format issue")


if __name__ == "__main__":
    asyncio.run(main())
