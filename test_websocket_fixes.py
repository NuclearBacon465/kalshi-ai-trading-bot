#!/usr/bin/env python3
"""
Test WebSocket fixes - CRITICAL TEST

This tests if the WebSocket connection works after fixing:
1. URL: wss://api.elections.kalshi.com (removed /trade-api/ws/v2)
2. Subscribe format: {"cmd": "subscribe", "params": {"channels": ["X"], "market_tickers": ["Y"]}}
3. New channels: market_positions, market_lifecycle_v2, communications
4. list_subscriptions command
5. unsubscribe command
"""

import asyncio
import json
from src.clients.kalshi_websocket import KalshiWebSocketClient
from src.clients.kalshi_client import KalshiClient
from src.utils.logging_setup import get_trading_logger

logger = get_trading_logger("websocket_test")


async def test_websocket_connection():
    """Test WebSocket connection with fixes."""
    logger.info("=" * 70)
    logger.info("TESTING WEBSOCKET FIXES")
    logger.info("=" * 70)

    kalshi_client = KalshiClient()
    ws_client = KalshiWebSocketClient(kalshi_client)

    try:
        # TEST 1: Connection
        logger.info("\n📡 TEST 1: WebSocket Connection")
        logger.info(f"URL: {ws_client.ws_url}")
        logger.info("Expected: wss://api.elections.kalshi.com")

        connected = await ws_client.connect()

        if connected:
            logger.info("✅ WebSocket CONNECTED successfully!")
        else:
            logger.error("❌ WebSocket connection FAILED")
            return

        # TEST 2: Subscribe to ticker (new format)
        logger.info("\n📊 TEST 2: Subscribe to Ticker (new cmd format)")

        # Get an open market first
        markets = await kalshi_client.get_markets(status='open', limit=1)
        if markets.get('markets'):
            test_ticker = markets['markets'][0]['ticker']
            logger.info(f"Using market: {test_ticker}")

            success = await ws_client.subscribe_ticker(test_ticker)
            if success:
                logger.info("✅ Ticker subscription sent (new format)")
            else:
                logger.error("❌ Ticker subscription failed")
        else:
            logger.warning("⚠️ No open markets available for testing")
            test_ticker = None

        # TEST 3: Subscribe to fills
        logger.info("\n🔔 TEST 3: Subscribe to Fill Notifications")
        success = await ws_client.subscribe_fills()
        if success:
            logger.info("✅ Fill subscription sent")
        else:
            logger.error("❌ Fill subscription failed")

        # TEST 4: Subscribe to market positions (NEW)
        logger.info("\n💼 TEST 4: Subscribe to Market Positions (NEW CHANNEL)")
        success = await ws_client.subscribe_market_positions()
        if success:
            logger.info("✅ Market positions subscription sent")
        else:
            logger.error("❌ Market positions subscription failed")

        # TEST 5: Subscribe to market lifecycle (NEW)
        logger.info("\n🔄 TEST 5: Subscribe to Market Lifecycle (NEW CHANNEL)")
        success = await ws_client.subscribe_market_lifecycle()
        if success:
            logger.info("✅ Market lifecycle subscription sent")
        else:
            logger.error("❌ Market lifecycle subscription failed")

        # TEST 6: List subscriptions (NEW COMMAND)
        logger.info("\n📋 TEST 6: List All Subscriptions (NEW COMMAND)")
        success = await ws_client.list_subscriptions()
        if success:
            logger.info("✅ list_subscriptions command sent")
        else:
            logger.error("❌ list_subscriptions command failed")

        # TEST 7: Wait for messages
        logger.info("\n⏳ TEST 7: Listening for Messages (10 seconds)...")
        logger.info("Expecting: subscription confirmations, possibly ticker updates")

        message_count = 0
        start_time = asyncio.get_event_loop().time()

        try:
            async with asyncio.timeout(10):
                async for message_str in ws_client.websocket:
                    try:
                        message = json.loads(message_str)
                        message_count += 1

                        msg_type = message.get('type', message.get('msg'))
                        channel = message.get('channel', 'N/A')

                        logger.info(f"📨 Message #{message_count}: type={msg_type}, channel={channel}")

                        # Show message details for important types
                        if msg_type in ['subscribed', 'unsubscribed', 'error', 'subscriptions']:
                            logger.info(f"   Details: {json.dumps(message, indent=2)}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")

        except asyncio.TimeoutError:
            logger.info(f"\n⏰ Timeout after 10 seconds. Received {message_count} messages.")

        # TEST 8: Unsubscribe (NEW COMMAND)
        if test_ticker:
            logger.info("\n🚫 TEST 8: Unsubscribe from Ticker (NEW COMMAND)")
            success = await ws_client.unsubscribe(["ticker"], [test_ticker])
            if success:
                logger.info("✅ Unsubscribe command sent")
            else:
                logger.error("❌ Unsubscribe command failed")

        # TEST 9: Disconnect
        logger.info("\n👋 TEST 9: Disconnect")
        await ws_client.disconnect()
        logger.info("✅ Disconnected")

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await kalshi_client.close()
        if ws_client.websocket:
            await ws_client.disconnect()

    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
