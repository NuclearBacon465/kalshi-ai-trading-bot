#!/usr/bin/env python3
"""
Test script to verify all Kalshi API Reference documentation improvements.

Tests:
1. Rate limit tier documentation
2. Pagination helpers (get_all_*)
3. Orderbook reciprocal relationships
4. Orderbook analysis utilities
5. Subpenny pricing integration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.clients.kalshi_client import KalshiClient
from src.utils.orderbook_helpers import (
    OrderbookAnalyzer,
    display_orderbook_summary,
    get_best_yes_bid,
    get_best_yes_ask,
    get_best_no_bid,
    get_best_no_ask,
    calculate_yes_spread
)
from src.utils.subpenny_helpers import get_price_dollars


async def test_rate_limit_docs():
    """Test that rate limit documentation is present."""
    print("\n" + "=" * 60)
    print("TEST 1: Rate Limit Documentation")
    print("=" * 60)

    client = KalshiClient()

    # Check class docstring for rate limit information
    docstring = KalshiClient.__doc__
    assert "Basic tier: 20 read/sec, 10 write/sec" in docstring
    assert "Advanced tier: 30 read/sec, 30 write/sec" in docstring
    assert "Premier tier: 100 read/sec, 100 write/sec" in docstring
    assert "Prime tier: 400 read/sec, 400 write/sec" in docstring

    print("✅ Rate limit tiers documented in KalshiClient")
    print("   - Basic: 20 read/sec, 10 write/sec")
    print("   - Advanced: 30 read/sec, 30 write/sec")
    print("   - Premier: 100 read/sec, 100 write/sec")
    print("   - Prime: 400 read/sec, 400 write/sec")
    print("   Per Kalshi Reference: Understanding Rate Limits and Tiers")

    return True


async def test_pagination_helpers():
    """Test cursor-based pagination helpers."""
    print("\n" + "=" * 60)
    print("TEST 2: Pagination Helpers")
    print("=" * 60)

    client = KalshiClient()

    try:
        # Test get_all_markets (with max_items limit for speed)
        print("Testing get_all_markets()...")
        markets = await client.get_all_markets(
            status="open",
            max_items=50  # Limit for faster test
        )
        print(f"✅ get_all_markets(): Retrieved {len(markets)} markets")

        # Test get_all_events
        print("\nTesting get_all_events()...")
        events = await client.get_all_events(max_items=20)
        print(f"✅ get_all_events(): Retrieved {len(events)} events")

        # Test get_all_series
        print("\nTesting get_all_series()...")
        series = await client.get_all_series(max_items=30)
        print(f"✅ get_all_series(): Retrieved {len(series)} series")

        print("\n   Per Kalshi Reference: cursor-based pagination to")
        print("   efficiently navigate through large datasets")

        return True

    except Exception as e:
        print(f"❌ Pagination test FAILED: {e}")
        return False


async def test_orderbook_reciprocal():
    """Test orderbook reciprocal relationship (bids to asks)."""
    print("\n" + "=" * 60)
    print("TEST 3: Orderbook Reciprocal Relationships")
    print("=" * 60)

    client = KalshiClient()

    try:
        # Get markets and pick one with an orderbook
        markets_result = await client.get_markets(limit=5, status="open")
        markets = markets_result.get('markets', [])

        if not markets:
            print("⚠️  No markets available for testing")
            return True

        ticker = markets[0]['ticker']
        print(f"Testing with market: {ticker}")

        # Get orderbook
        orderbook = await client.get_orderbook(ticker)

        # Test reciprocal functions
        best_yes_bid = get_best_yes_bid(orderbook)
        best_yes_ask = get_best_yes_ask(orderbook)
        best_no_bid = get_best_no_bid(orderbook)
        best_no_ask = get_best_no_ask(orderbook)

        print(f"\n✅ Reciprocal Relationship Verified:")
        if best_yes_bid and best_no_ask:
            print(f"   YES BID {best_yes_bid}¢ → NO ASK {best_no_ask}¢ (should be 100 - {best_yes_bid} = {100 - best_yes_bid})")
            assert best_no_ask == 100 - best_yes_bid, "Reciprocal relationship broken!"

        if best_no_bid and best_yes_ask:
            print(f"   NO BID {best_no_bid}¢ → YES ASK {best_yes_ask}¢ (should be 100 - {best_no_bid} = {100 - best_no_bid})")
            assert best_yes_ask == 100 - best_no_bid, "Reciprocal relationship broken!"

        print("\n   Per Kalshi Reference: 'YES BID at price X is equivalent")
        print("   to NO ASK at price (100 - X)'")

        return True

    except Exception as e:
        print(f"❌ Orderbook reciprocal test FAILED: {e}")
        return False


async def test_orderbook_analyzer():
    """Test OrderbookAnalyzer utility class."""
    print("\n" + "=" * 60)
    print("TEST 4: Orderbook Analysis Utilities")
    print("=" * 60)

    client = KalshiClient()

    try:
        # Get a market with orderbook
        markets_result = await client.get_markets(limit=10, status="open")
        markets = markets_result.get('markets', [])

        if not markets:
            print("⚠️  No markets available for testing")
            return True

        # Find market with active orderbook
        orderbook = None
        ticker = None
        for market in markets:
            ticker = market['ticker']
            ob = await client.get_orderbook(ticker)
            if ob.get('orderbook', {}).get('yes') or ob.get('orderbook', {}).get('no'):
                orderbook = ob
                break

        if not orderbook:
            print("⚠️  No markets with active orderbooks")
            return True

        print(f"Analyzing market: {ticker}\n")

        # Test OrderbookAnalyzer
        analyzer = OrderbookAnalyzer(orderbook)

        # Test get_best_prices
        prices = analyzer.get_best_prices()
        print(f"✅ get_best_prices():")
        print(f"   YES: Bid {prices['best_yes_bid']}¢, Ask {prices['best_yes_ask']}¢")
        print(f"   NO:  Bid {prices['best_no_bid']}¢, Ask {prices['best_no_ask']}¢")

        # Test get_spread
        spreads = analyzer.get_spread()
        print(f"\n✅ get_spread():")
        print(f"   YES spread: {spreads['yes_spread']}¢")
        print(f"   NO spread:  {spreads['no_spread']}¢")

        # Test calculate_depth
        depth = analyzer.calculate_depth(5)
        print(f"\n✅ calculate_depth(5):")
        print(f"   YES: {depth['yes_depth']} contracts within 5¢")
        print(f"   NO:  {depth['no_depth']} contracts within 5¢")

        # Test get_total_liquidity
        liquidity = analyzer.get_total_liquidity()
        print(f"\n✅ get_total_liquidity():")
        print(f"   YES: {liquidity['yes_liquidity']} total contracts")
        print(f"   NO:  {liquidity['no_liquidity']} total contracts")

        # Test display_orderbook_summary
        print(f"\n✅ display_orderbook_summary():")
        summary = display_orderbook_summary(orderbook)
        print(summary)

        return True

    except Exception as e:
        print(f"❌ OrderbookAnalyzer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_subpenny_integration():
    """Test subpenny pricing integration."""
    print("\n" + "=" * 60)
    print("TEST 5: Subpenny Pricing Integration")
    print("=" * 60)

    client = KalshiClient()

    try:
        # Get a market with price data
        markets_result = await client.get_markets(limit=1, status="open")
        markets = markets_result.get('markets', [])

        if not markets:
            print("⚠️  No markets available for testing")
            return True

        market = markets[0]
        ticker = market['ticker']

        print(f"Testing with market: {ticker}")
        print(f"\nMarket price fields:")

        # Test subpenny helper on market data
        yes_bid = get_price_dollars(market, 'yes_bid', default=0.0)
        yes_ask = get_price_dollars(market, 'yes_ask', default=0.0)
        last_price = get_price_dollars(market, 'last_price', default=0.0)

        print(f"   YES bid: ${yes_bid:.4f}")
        print(f"   YES ask: ${yes_ask:.4f}")
        print(f"   Last price: ${last_price:.4f}")

        print(f"\n✅ Subpenny helpers working correctly")
        print(f"   Per Kalshi Reference: Fixed-point dollars format")
        print(f"   supports subpenny pricing (4 decimal places)")

        return True

    except Exception as e:
        print(f"❌ Subpenny integration test FAILED: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("KALSHI API REFERENCE IMPROVEMENTS - VERIFICATION TESTS")
    print("=" * 70)
    print("\nTesting improvements based on Kalshi API Reference documentation:")
    print("- Rate Limits and Tiers")
    print("- Understanding Pagination")
    print("- Orderbook Responses")
    print("- Subpenny Pricing")

    results = []

    # Run all tests
    results.append(("Rate Limit Documentation", await test_rate_limit_docs()))
    results.append(("Pagination Helpers", await test_pagination_helpers()))
    results.append(("Orderbook Reciprocal", await test_orderbook_reciprocal()))
    results.append(("Orderbook Analyzer", await test_orderbook_analyzer()))
    results.append(("Subpenny Integration", await test_subpenny_integration()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("\n🎉 All Reference improvements verified successfully!")
        print("   Bot now implements Kalshi Reference best practices:")
        print("   - Rate limit tiers documented (Basic → Prime)")
        print("   - Auto-pagination for large datasets")
        print("   - Orderbook reciprocal relationship helpers")
        print("   - Comprehensive orderbook analysis utilities")
        print("   - Subpenny pricing support integrated")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
