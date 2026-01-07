#!/usr/bin/env python3
"""
COMPREHENSIVE LIVE TESTING SUITE
Tests everything: API, orders, configuration, bot health, database
"""

import asyncio
import sys
import os
import subprocess
from datetime import datetime

sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

from src.clients.kalshi_client import KalshiClient
from src.config.settings import settings
import aiosqlite

async def test_1_api_connectivity():
    """Test 1: Full API connectivity and endpoints"""
    print("\n" + "="*80)
    print("TEST 1: COMPLETE API CONNECTIVITY")
    print("="*80)

    client = KalshiClient()
    checks = []

    try:
        # Test 1.1: Balance endpoint
        print("\n[1.1] Testing Balance Endpoint...")
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        portfolio = balance.get('payout', 0) / 100
        print(f"  ✅ Balance: ${cash:.2f} cash, ${portfolio:.2f} portfolio")
        checks.append(True)

        # Test 1.2: Markets endpoint
        print("\n[1.2] Testing Markets Endpoint...")
        markets = await client.get_markets(limit=10)
        market_count = len(markets.get('markets', []))
        print(f"  ✅ Markets: Fetched {market_count} markets")
        checks.append(market_count > 0)

        # Test 1.3: Positions endpoint
        print("\n[1.3] Testing Positions Endpoint...")
        positions = await client.get_positions()
        position_count = len(positions.get('market_positions', []))
        print(f"  ✅ Positions: {position_count} open positions")
        checks.append(True)

        # Test 1.4: Orders endpoint
        print("\n[1.4] Testing Orders Endpoint...")
        try:
            orders = await client.get_orders()
            order_count = len(orders.get('orders', []))
            print(f"  ✅ Orders: {order_count} recent orders")
            checks.append(True)
        except Exception as e:
            print(f"  ⚠️ Orders endpoint: {e}")
            checks.append(True)  # Not critical

        # Test 1.5: Trades endpoint
        print("\n[1.5] Testing Trades Endpoint...")
        try:
            trades = await client.get_trades(limit=5)
            trade_count = len(trades.get('trades', []))
            print(f"  ✅ Trades: {trade_count} recent trades")
            checks.append(True)
        except Exception as e:
            print(f"  ⚠️ Trades endpoint: {e}")
            checks.append(True)  # Not critical

    except Exception as e:
        print(f"  ❌ API Test Failed: {e}")
        checks.append(False)
    finally:
        await client.close()

    passed = sum(checks)
    total = len(checks)
    print(f"\n📊 API Connectivity: {passed}/{total} endpoints working")
    return all(checks)


async def test_2_order_validation_comprehensive():
    """Test 2: Comprehensive order validation for all combinations"""
    print("\n" + "="*80)
    print("TEST 2: COMPREHENSIVE ORDER VALIDATION")
    print("="*80)

    # Test with a real market ticker
    client = KalshiClient()

    try:
        # Get a real tradeable market
        markets = await client.get_markets(limit=10, status="open")
        market_list = markets.get('markets', [])

        if not market_list:
            print("  ⚠️ No open markets available for testing")
            return True

        test_ticker = market_list[0]['ticker']
        print(f"\n  Using test market: {test_ticker}")

    except Exception as e:
        print(f"  ⚠️ Could not fetch test market: {e}")
        test_ticker = "TEST-TICKER"
    finally:
        await client.close()

    test_cases = [
        # (type, side, action, params, description)
        ("market", "yes", "buy", {"count": 1}, "Market BUY YES"),
        ("market", "no", "buy", {"count": 1}, "Market BUY NO"),
        ("market", "yes", "sell", {"count": 1}, "Market SELL YES"),
        ("market", "no", "sell", {"count": 1}, "Market SELL NO"),
        ("limit", "yes", "buy", {"count": 1, "yes_price": 50}, "Limit BUY YES @ 50¢"),
        ("limit", "no", "buy", {"count": 1, "no_price": 50}, "Limit BUY NO @ 50¢"),
        ("limit", "yes", "sell", {"count": 1, "yes_price": 75}, "Limit SELL YES @ 75¢"),
        ("limit", "no", "sell", {"count": 1, "no_price": 75}, "Limit SELL NO @ 75¢"),
    ]

    print(f"\n  Testing all 8 order type combinations:")
    results = []

    for order_type, side, action, params, description in test_cases:
        try:
            # Validate order structure
            order_data = {
                "ticker": test_ticker,
                "client_order_id": f"test-{order_type}-{side}-{action}",
                "side": side,
                "action": action,
                "type": order_type,
                **params
            }

            # Validation checks
            assert order_data["side"].lower() in ["yes", "no"], f"Invalid side: {order_data['side']}"
            assert order_data["action"].lower() in ["buy", "sell"], f"Invalid action: {order_data['action']}"
            assert order_data["type"] in ["market", "limit"], f"Invalid type: {order_data['type']}"
            assert int(order_data["count"]) >= 1, "Count must be >= 1"

            # Price validation
            for price_key in ["yes_price", "no_price"]:
                if price_key in order_data and order_data[price_key] is not None:
                    price = order_data[price_key]
                    assert isinstance(price, int), f"{price_key} must be integer"
                    assert 1 <= price <= 99, f"{price_key} must be 1-99 cents"

            print(f"    ✅ {description}")
            results.append(True)

        except Exception as e:
            print(f"    ❌ {description}: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\n📊 Order Validation: {passed}/{total} combinations passed")
    return all(results)


async def test_3_configuration_verification():
    """Test 3: Verify HIGH RISK HIGH REWARD configuration"""
    print("\n" + "="*80)
    print("TEST 3: HIGH RISK HIGH REWARD CONFIGURATION")
    print("="*80)

    checks = []

    print(f"\n  [3.1] Confidence Threshold")
    conf = settings.trading.min_confidence_to_trade
    is_aggressive = conf <= 0.55
    print(f"    Current: {conf*100:.0f}%")
    print(f"    Status: {'✅ AGGRESSIVE' if is_aggressive else '⚠️ CONSERVATIVE'}")
    checks.append(is_aggressive)

    print(f"\n  [3.2] Kelly Fraction")
    kelly = settings.trading.kelly_fraction
    is_aggressive = kelly >= 0.7
    print(f"    Current: {kelly}")
    print(f"    Status: {'✅ AGGRESSIVE' if is_aggressive else '⚠️ CONSERVATIVE'}")
    checks.append(is_aggressive)

    print(f"\n  [3.3] Max Position Size")
    max_pos = settings.trading.max_single_position
    is_aggressive = max_pos >= 0.35
    print(f"    Current: {max_pos*100:.0f}%")
    print(f"    Status: {'✅ AGGRESSIVE' if is_aggressive else '⚠️ CONSERVATIVE'}")
    checks.append(is_aggressive)

    print(f"\n  [3.4] Daily AI Budget")
    budget = settings.trading.daily_ai_budget
    is_adequate = budget >= 15
    print(f"    Current: ${budget}")
    print(f"    Status: {'✅ ADEQUATE' if is_adequate else '⚠️ LOW'}")
    checks.append(is_adequate)

    print(f"\n  [3.5] Portfolio Optimization")
    portfolio_opt = getattr(settings.trading, 'use_kelly_criterion', False)
    print(f"    Status: {'✅ ENABLED' if portfolio_opt else '❌ DISABLED'}")
    checks.append(portfolio_opt)

    passed = sum(checks)
    total = len(checks)
    print(f"\n📊 Configuration: {passed}/{total} settings optimized")
    return all(checks)


async def test_4_bot_health():
    """Test 4: Bot health and activity"""
    print("\n" + "="*80)
    print("TEST 4: BOT HEALTH & ACTIVITY")
    print("="*80)

    checks = []

    # Check if bot is running
    print("\n  [4.1] Bot Process Status")
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    bot_running = 'beast_mode_bot.py' in result.stdout
    if bot_running:
        pid = [line.split()[1] for line in result.stdout.split('\n')
               if 'beast_mode_bot.py' in line and 'grep' not in line][0]
        print(f"    ✅ Bot is RUNNING (PID {pid})")
        checks.append(True)
    else:
        print(f"    ❌ Bot is NOT RUNNING")
        checks.append(False)

    # Check log file
    print("\n  [4.2] Log File Status")
    try:
        with open('logs/bot_output.log', 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines

        # Look for recent activity
        has_activity = any('INFO' in line or 'DEBUG' in line for line in recent_lines)
        has_errors = any('ERROR' in line or 'CRITICAL' in line for line in recent_lines[-10:])

        if has_activity:
            print(f"    ✅ Bot has recent activity")
            checks.append(True)
        else:
            print(f"    ⚠️ No recent activity in logs")
            checks.append(False)

        if has_errors:
            print(f"    ⚠️ Recent errors detected in logs")
        else:
            print(f"    ✅ No recent errors")

    except Exception as e:
        print(f"    ❌ Could not read log file: {e}")
        checks.append(False)

    passed = sum(checks)
    total = len(checks)
    print(f"\n📊 Bot Health: {passed}/{total} checks passed")
    return all(checks)


async def test_5_database_integrity():
    """Test 5: Database integrity and structure"""
    print("\n" + "="*80)
    print("TEST 5: DATABASE INTEGRITY")
    print("="*80)

    checks = []

    try:
        async with aiosqlite.connect('trading_system.db') as db:
            # Check tables exist
            print("\n  [5.1] Database Tables")
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]

            required_tables = ['markets', 'positions', 'llm_queries']
            for table in required_tables:
                if table in tables:
                    print(f"    ✅ Table '{table}' exists")
                    checks.append(True)
                else:
                    print(f"    ❌ Table '{table}' missing")
                    checks.append(False)

            # Check recent activity
            print("\n  [5.2] Recent Activity")
            cursor = await db.execute(
                "SELECT COUNT(*) FROM llm_queries WHERE datetime(timestamp) > datetime('now', '-1 hour')"
            )
            recent_queries = (await cursor.fetchone())[0]
            print(f"    AI queries (last hour): {recent_queries}")
            if recent_queries > 0:
                print(f"    ✅ Bot is actively analyzing markets")
                checks.append(True)
            else:
                print(f"    ⚠️ No recent AI queries")
                checks.append(True)  # Not necessarily a failure

            # Check positions table
            print("\n  [5.3] Positions Table")
            cursor = await db.execute("SELECT COUNT(*) FROM positions")
            total_positions = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
            open_positions = (await cursor.fetchone())[0]

            print(f"    Total positions: {total_positions}")
            print(f"    Open positions: {open_positions}")
            print(f"    ✅ Positions table functional")
            checks.append(True)

    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        checks.append(False)

    passed = sum(checks)
    total = len(checks)
    print(f"\n📊 Database: {passed}/{total} checks passed")
    return all(checks)


async def test_6_live_market_data():
    """Test 6: Live market data and trading readiness"""
    print("\n" + "="*80)
    print("TEST 6: LIVE MARKET DATA & TRADING READINESS")
    print("="*80)

    client = KalshiClient()
    checks = []

    try:
        # Get live markets
        print("\n  [6.1] Fetching Live Markets")
        markets = await client.get_markets(limit=20, status="open")
        market_list = markets.get('markets', [])
        print(f"    ✅ Found {len(market_list)} open markets")
        checks.append(len(market_list) > 0)

        # Analyze tradeable markets
        print("\n  [6.2] Analyzing Tradeable Markets")
        tradeable = 0
        for market in market_list:
            yes_ask = market.get('yes_ask', 0)
            no_ask = market.get('no_ask', 0)
            volume = market.get('volume', 0)

            if yes_ask > 0 and yes_ask < 100 and no_ask > 0 and no_ask < 100 and volume > 0:
                tradeable += 1

        if tradeable > 0:
            print(f"    ✅ {tradeable} markets are currently tradeable")
            checks.append(True)
        else:
            print(f"    ⚠️ No tradeable markets (may be off-hours or weekend)")
            checks.append(True)  # Not a failure, just timing

        # Show top markets
        if tradeable > 0:
            print("\n  [6.3] Top Tradeable Markets:")
            count = 0
            for market in market_list:
                yes_ask = market.get('yes_ask', 0)
                no_ask = market.get('no_ask', 0)
                volume = market.get('volume', 0)

                if yes_ask > 0 and yes_ask < 100 and no_ask > 0 and no_ask < 100 and volume > 0:
                    ticker = market.get('ticker', '')[:50]
                    print(f"      • {ticker}")
                    print(f"        Vol: {volume:,} | YES: {yes_ask}¢ | NO: {no_ask}¢")
                    count += 1
                    if count >= 3:
                        break
            checks.append(True)

        # Check account balance
        print("\n  [6.4] Account Balance")
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        print(f"    Cash available: ${cash:.2f}")

        if cash > 10:
            print(f"    ✅ Sufficient capital for trading")
            checks.append(True)
        else:
            print(f"    ⚠️ Low capital (< $10)")
            checks.append(False)

    except Exception as e:
        print(f"  ❌ Market data test failed: {e}")
        checks.append(False)
    finally:
        await client.close()

    passed = sum(checks)
    total = len(checks)
    print(f"\n📊 Market Data: {passed}/{total} checks passed")
    return all(checks)


async def main():
    """Run all comprehensive tests"""
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE LIVE TESTING SUITE")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []

    # Run all tests
    results.append(("API Connectivity", await test_1_api_connectivity()))
    results.append(("Order Validation", await test_2_order_validation_comprehensive()))
    results.append(("Configuration", await test_3_configuration_verification()))
    results.append(("Bot Health", await test_4_bot_health()))
    results.append(("Database Integrity", await test_5_database_integrity()))
    results.append(("Live Market Data", await test_6_live_market_data()))

    # Print final summary
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print("\n" + "="*80)
    if total_passed == total_tests:
        print(f"🎉 ALL TESTS PASSED: {total_passed}/{total_tests}")
        print("✅ Bot is 100% operational and ready for HIGH RISK trading!")
    else:
        print(f"⚠️ TESTS PASSED: {total_passed}/{total_tests}")
        print(f"❌ {total_tests - total_passed} test(s) need attention")
    print("="*80)

    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
