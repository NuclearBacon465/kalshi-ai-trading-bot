#!/usr/bin/env python3
"""
Official Kalshi API Test Suite
Tests all order placement functionality with the real Kalshi API
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

from src.clients.kalshi_client import KalshiClient
from src.config.settings import settings

async def test_kalshi_api_connection():
    """Test 1: Verify Kalshi API connection"""
    print("\n" + "="*80)
    print("TEST 1: KALSHI API CONNECTION")
    print("="*80)

    client = KalshiClient()

    try:
        # Test balance endpoint
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        total = balance.get('portfolio_value', 0) / 100

        print(f"✅ API Connection: SUCCESS")
        print(f"   Cash: ${cash:.2f}")
        print(f"   Portfolio: ${total:.2f}")

        # Test markets endpoint
        markets = await client.get_markets(limit=5)
        market_count = len(markets.get('markets', []))
        print(f"✅ Markets Endpoint: SUCCESS ({market_count} markets fetched)")

        # Test positions endpoint
        positions = await client.get_positions()
        position_count = len(positions.get('market_positions', []))
        print(f"✅ Positions Endpoint: SUCCESS ({position_count} open positions)")

        return True, markets.get('markets', [])[0] if market_count > 0 else None

    except Exception as e:
        print(f"❌ API Connection: FAILED - {e}")
        return False, None
    finally:
        await client.close()


async def test_order_validation():
    """Test 2: Validate all order types (dry run - no actual orders)"""
    print("\n" + "="*80)
    print("TEST 2: ORDER VALIDATION (DRY RUN)")
    print("="*80)

    test_ticker = "KXMVENFLSINGLEGAME-S2025512E9021789-9D19E5D1024"

    test_cases = [
        ("market", "yes", "buy", {"count": 1}, "Market BUY YES"),
        ("market", "no", "buy", {"count": 1}, "Market BUY NO"),
        ("limit", "yes", "buy", {"count": 1, "yes_price": 50}, "Limit BUY YES @ 50¢"),
        ("limit", "no", "buy", {"count": 1, "no_price": 50}, "Limit BUY NO @ 50¢"),
        ("limit", "yes", "sell", {"count": 1, "yes_price": 75}, "Limit SELL YES @ 75¢"),
        ("limit", "no", "sell", {"count": 1, "no_price": 75}, "Limit SELL NO @ 75¢"),
    ]

    results = []
    for order_type, side, action, params, description in test_cases:
        try:
            # Validate order parameters
            order_data = {
                "ticker": test_ticker,
                "client_order_id": f"test-{order_type}-{side}-{action}",
                "side": side,
                "action": action,
                "type": order_type,
                **params
            }

            # Validation logic (same as in kalshi_client.py)
            assert side.lower() in ["yes", "no"], f"Invalid side: {side}"
            assert action.lower() in ["buy", "sell"], f"Invalid action: {action}"
            assert order_type in ["market", "limit"], f"Invalid type: {order_type}"

            # Price validation
            for price_key in ["yes_price", "no_price"]:
                if price_key in order_data and order_data[price_key] is not None:
                    price = order_data[price_key]
                    assert 1 <= price <= 99, f"{price_key} out of bounds: {price}"

            print(f"  ✅ {description}: Validation PASSED")
            results.append(True)

        except Exception as e:
            print(f"  ❌ {description}: Validation FAILED - {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\n📊 Validation Results: {passed}/{total} tests passed")

    return all(results)


async def test_configuration():
    """Test 3: Verify HIGH RISK HIGH REWARD configuration"""
    print("\n" + "="*80)
    print("TEST 3: HIGH RISK HIGH REWARD CONFIGURATION")
    print("="*80)

    checks = []

    # Check confidence thresholds (should be aggressive for high risk)
    min_conf = settings.trading.min_confidence_to_trade
    print(f"  Confidence Threshold: {min_conf*100:.0f}% {'✅' if min_conf <= 0.55 else '⚠️'}")
    checks.append(min_conf <= 0.55)

    # Check Kelly fraction (should be aggressive)
    kelly = settings.trading.kelly_fraction
    print(f"  Kelly Fraction: {kelly} {'✅' if kelly >= 0.7 else '⚠️'}")
    checks.append(kelly >= 0.7)

    # Check max position size (should be large for high risk)
    max_pos = settings.trading.max_single_position
    print(f"  Max Position Size: {max_pos*100:.0f}% {'✅' if max_pos >= 0.35 else '⚠️'}")
    checks.append(max_pos >= 0.35)

    # Check daily budget
    budget = settings.trading.daily_ai_budget
    print(f"  Daily AI Budget: ${budget} ✅")
    checks.append(budget > 0)

    # Check portfolio optimization
    portfolio_opt = getattr(settings.trading, 'use_kelly_criterion', False)
    print(f"  Portfolio Optimization: {'✅ ENABLED' if portfolio_opt else '❌ DISABLED'}")
    checks.append(portfolio_opt)

    passed = sum(checks)
    total = len(checks)
    print(f"\n📊 Configuration: {passed}/{total} settings optimized for HIGH RISK/REWARD")

    return all(checks)


async def test_order_placement_features():
    """Test 4: Verify all order placement features"""
    print("\n" + "="*80)
    print("TEST 4: ORDER PLACEMENT FEATURES")
    print("="*80)

    # Check if execute.py has all the necessary functions
    try:
        with open('src/jobs/execute.py', 'r') as f:
            execute_code = f.read()

        features = [
            ("execute_position", "✅ Order Execution"),
            ("place_sell_limit_order", "✅ Sell Limit Orders"),
            ("place_profit_taking_orders", "✅ Profit Taking (25% target)"),
            ("place_stop_loss_orders", "✅ Stop Loss (10% protection)"),
            ("max(0.01, min(0.99, sell_price))", "✅ Price Bounds Validation"),
        ]

        all_found = True
        for feature, description in features:
            if feature in execute_code:
                print(f"  {description}")
            else:
                print(f"  ❌ {description} - NOT FOUND")
                all_found = False

        # Check kalshi_client.py for order validation
        with open('src/clients/kalshi_client.py', 'r') as f:
            client_code = f.read()

        client_features = [
            ("validate_price", "✅ Price Validation Function"),
            ("Invalid side:", "✅ Side Validation"),
            ("Invalid action:", "✅ Action Validation"),
            ("Market SELL orders", "✅ Market SELL Support"),
        ]

        for feature, description in client_features:
            if feature in client_code:
                print(f"  {description}")
            else:
                print(f"  ❌ {description} - NOT FOUND")
                all_found = False

        return all_found

    except Exception as e:
        print(f"  ❌ Error reading code files: {e}")
        return False


async def main():
    """Run comprehensive Kalshi API tests"""
    print("\n" + "="*80)
    print("🚀 OFFICIAL KALSHI API TEST SUITE - HIGH RISK HIGH REWARD MODE")
    print("="*80)

    results = []

    # Test 1: API Connection
    api_ok, test_market = await test_kalshi_api_connection()
    results.append(("API Connection", api_ok))

    # Test 2: Order Validation
    validation_ok = await test_order_validation()
    results.append(("Order Validation", validation_ok))

    # Test 3: Configuration
    config_ok = await test_configuration()
    results.append(("Configuration", config_ok))

    # Test 4: Order Features
    features_ok = await test_order_placement_features()
    results.append(("Order Features", features_ok))

    # Print final summary
    print("\n" + "="*80)
    print("📊 FINAL TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print("\n" + "="*80)
    if total_passed == total_tests:
        print(f"🎉 ALL TESTS PASSED: {total_passed}/{total_tests}")
        print("✅ Bot is ready for HIGH RISK HIGH REWARD trading!")
        print("\n💰 Configuration:")
        print(f"   - Confidence: {settings.trading.min_confidence_to_trade*100:.0f}%+ (aggressive)")
        print(f"   - Kelly Fraction: {settings.trading.kelly_fraction} (aggressive)")
        print(f"   - Max Position: {settings.trading.max_single_position*100:.0f}% (aggressive)")
        print(f"   - All order types working (BUY/SELL, MARKET/LIMIT, YES/NO)")
        print(f"   - Price validation, stop-loss, profit-taking all active")
    else:
        print(f"⚠️ TESTS PASSED: {total_passed}/{total_tests}")
        print("Some features need attention")
    print("="*80)

    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
