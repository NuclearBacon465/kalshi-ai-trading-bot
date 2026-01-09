#!/usr/bin/env python3
"""
Test REST API fixes and new endpoints.

Tests:
1. GET /portfolio/settlements (new)
2. GET /events (standard events)
3. GET /events/multivariate (new, combo markets)
4. Subpenny pricing helpers
"""

import asyncio
from src.clients.kalshi_client import KalshiClient
from src.utils.subpenny_helpers import (
    get_price_dollars,
    get_all_prices_dollars,
    is_using_subpenny_format,
    format_price_for_display,
    convert_centi_cents_to_dollars
)
from src.utils.logging_setup import get_trading_logger

logger = get_trading_logger("rest_api_test")


async def test_rest_api():
    """Test REST API fixes."""
    logger.info("=" * 70)
    logger.info("TESTING REST API FIXES")
    logger.info("=" * 70)

    client = KalshiClient()

    try:
        # TEST 1: GET /portfolio/settlements (NEW ENDPOINT)
        logger.info("\n💰 TEST 1: GET /portfolio/settlements (NEW ENDPOINT)")
        logger.info("This endpoint returns SETTLED positions (get_positions returns unsettled)")

        try:
            settlements = await client.get_settlements(limit=5)
            settlement_list = settlements.get('settlements', [])
            logger.info(f"✅ Settlements retrieved: {len(settlement_list)} positions")

            if settlement_list:
                logger.info("\nSample settlement:")
                sample = settlement_list[0]
                logger.info(f"  Market: {sample.get('market_ticker', 'N/A')}")
                logger.info(f"  Event: {sample.get('event_ticker', 'N/A')}")
                logger.info(f"  Revenue: ${sample.get('revenue', 0)/100:.2f}")
                logger.info(f"  Fees Paid: ${sample.get('fees_paid', 0)/100:.2f}")
            else:
                logger.info("  No settled positions yet")

        except Exception as e:
            logger.error(f"❌ Settlements endpoint failed: {e}")

        # TEST 2: GET /events (EXCLUDES multivariate as of Nov 6, 2025)
        logger.info("\n📅 TEST 2: GET /events (standard events, excludes multivariate)")

        try:
            events = await client.get_events(status='open', limit=3)
            event_list = events.get('events', [])
            logger.info(f"✅ Events retrieved: {len(event_list)} events")

            if event_list:
                logger.info("\nSample event:")
                sample = event_list[0]
                logger.info(f"  Ticker: {sample.get('event_ticker', 'N/A')}")
                logger.info(f"  Title: {sample.get('title', 'N/A')}")
                logger.info(f"  Markets: {len(sample.get('markets', []))}")

        except Exception as e:
            logger.error(f"❌ Events endpoint failed: {e}")

        # TEST 3: GET /events/multivariate (NEW ENDPOINT for combo markets)
        logger.info("\n🎲 TEST 3: GET /events/multivariate (NEW ENDPOINT)")

        try:
            mve_events = await client.get_multivariate_events(limit=3)
            mve_list = mve_events.get('events', [])
            logger.info(f"✅ Multivariate events retrieved: {len(mve_list)} events")

            if mve_list:
                logger.info("\nSample multivariate event:")
                sample = mve_list[0]
                logger.info(f"  Ticker: {sample.get('event_ticker', 'N/A')}")
                logger.info(f"  Title: {sample.get('title', 'N/A')}")
        except Exception as e:
            logger.info(f"⚠️ Multivariate events endpoint: {e}")
            logger.info("   (May not have multivariate events available)")

        # TEST 4: Subpenny Pricing Helpers
        logger.info("\n💵 TEST 4: Subpenny Pricing Helpers")

        # Get a market to test with
        markets = await client.get_markets(status='open', limit=1)
        if markets.get('markets'):
            market = markets['markets'][0]
            ticker = market.get('ticker', 'N/A')

            logger.info(f"\nTesting with market: {ticker}")

            # Check if using subpenny format
            using_subpenny = is_using_subpenny_format(market)
            logger.info(f"✅ Using subpenny format: {using_subpenny}")

            # Get prices using helper
            yes_bid = get_price_dollars(market, 'yes_bid')
            yes_ask = get_price_dollars(market, 'yes_ask')
            no_bid = get_price_dollars(market, 'no_bid')
            no_ask = get_price_dollars(market, 'no_ask')

            logger.info(f"\nPrices extracted:")
            logger.info(f"  Yes: {format_price_for_display(yes_bid)} / {format_price_for_display(yes_ask)}")
            logger.info(f"  No:  {format_price_for_display(no_bid)} / {format_price_for_display(no_ask)}")

            # Get all prices at once
            all_prices = get_all_prices_dollars(market)
            if 'yes_spread' in all_prices:
                logger.info(f"  Yes Spread: {format_price_for_display(all_prices['yes_spread'])}")
                logger.info(f"  Yes Mid: {format_price_for_display(all_prices['yes_mid'])}")

            # Test centi-cents conversion
            logger.info(f"\nCenti-cents conversion test:")
            logger.info(f"  55000 centi-cents = ${convert_centi_cents_to_dollars(55000):.4f}")
            logger.info(f"  10000 centi-cents = ${convert_centi_cents_to_dollars(10000):.4f}")

            # Show raw market data for verification
            if using_subpenny:
                logger.info(f"\n✅ Market has subpenny fields:")
                if 'yes_bid_dollars' in market:
                    logger.info(f"  yes_bid_dollars: {market['yes_bid_dollars']}")
                if 'yes_ask_dollars' in market:
                    logger.info(f"  yes_ask_dollars: {market['yes_ask_dollars']}")
            else:
                logger.info(f"\n⚠️ Market using OLD cent fields (deprecated Jan 15, 2026):")
                if 'yes_bid' in market:
                    logger.info(f"  yes_bid: {market['yes_bid']} cents")
                if 'yes_ask' in market:
                    logger.info(f"  yes_ask: {market['yes_ask']} cents")

        else:
            logger.warning("⚠️ No open markets available for subpenny testing")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()

    logger.info("\n" + "=" * 70)
    logger.info("REST API TEST COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_rest_api())
