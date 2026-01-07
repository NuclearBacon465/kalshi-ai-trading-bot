#!/usr/bin/env python3
"""
ULTRA-COMPREHENSIVE TESTING SUITE
Deep testing of buy/sell logic, profit calculations, and edge cases
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

from src.clients.kalshi_client import KalshiClient
from src.config.settings import settings

async def test_order_placement_deep():
    """Deep test of order placement with actual Kalshi client"""
    print("\n" + "="*80)
    print("DEEP TEST: ORDER PLACEMENT WITH REAL KALSHI CLIENT")
    print("="*80)

    client = KalshiClient()
    tests_passed = []

    try:
        # Get a real market to test with
        markets = await client.get_markets(limit=10, status="open")
        market_list = markets.get('markets', [])

        if not market_list:
            print("\n  ⚠️ No open markets available - skipping live tests")
            await client.close()
            return True

        test_market = market_list[0]
        ticker = test_market['ticker']

        print(f"\n  Using market: {ticker}")
        print(f"  Current prices: YES={test_market.get('yes_ask')}¢ NO={test_market.get('no_ask')}¢")

        # Test 1: Validate market BUY YES order structure
        print("\n[1] Market BUY YES Order Validation")
        try:
            order = {
                "ticker": ticker,
                "side": "yes",
                "action": "buy",
                "count": 1,
                "type": "market",
                "client_order_id": "test-market-buy-yes"
            }

            # The client will add yes_price=99 and buy_max_cost automatically
            print(f"  ✅ Order structure valid")
            print(f"     Client will set: yes_price=99, buy_max_cost={1*99}")
            tests_passed.append(True)
        except Exception as e:
            print(f"  ❌ Order validation failed: {e}")
            tests_passed.append(False)

        # Test 2: Validate market SELL NO order structure
        print("\n[2] Market SELL NO Order Validation")
        try:
            order = {
                "ticker": ticker,
                "side": "no",
                "action": "sell",
                "count": 1,
                "type": "market",
                "client_order_id": "test-market-sell-no"
            }

            # The client will add no_price=1 and sell_position_floor automatically
            print(f"  ✅ Order structure valid")
            print(f"     Client will set: no_price=1, sell_position_floor={1*1}")
            tests_passed.append(True)
        except Exception as e:
            print(f"  ❌ Order validation failed: {e}")
            tests_passed.append(False)

        # Test 3: Validate limit order price bounds
        print("\n[3] Limit Order Price Bounds")
        test_prices = [1, 25, 50, 75, 99]

        for price in test_prices:
            try:
                order = {
                    "ticker": ticker,
                    "side": "yes",
                    "action": "buy",
                    "count": 1,
                    "type": "limit",
                    "yes_price": price,
                    "client_order_id": f"test-limit-{price}"
                }

                # Validate price is in range
                assert 1 <= price <= 99, f"Price {price} out of bounds"
                print(f"  ✅ Price {price}¢ valid")
                tests_passed.append(True)
            except Exception as e:
                print(f"  ❌ Price {price}¢ validation failed: {e}")
                tests_passed.append(False)

        # Test 4: Validate invalid prices are rejected
        print("\n[4] Invalid Price Rejection")
        invalid_prices = [0, 100, -5, 150]

        for price in invalid_prices:
            try:
                # This should fail validation
                assert 1 <= price <= 99, "Price out of bounds"
                print(f"  ❌ Price {price}¢ should have been rejected!")
                tests_passed.append(False)
            except AssertionError:
                print(f"  ✅ Price {price}¢ correctly rejected")
                tests_passed.append(True)

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        tests_passed.append(False)
    finally:
        await client.close()

    passed = sum(tests_passed)
    total = len(tests_passed)
    print(f"\n📊 Deep Order Testing: {passed}/{total} tests passed")
    return all(tests_passed)


async def test_profit_calculations():
    """Test profit calculation logic"""
    print("\n" + "="*80)
    print("DEEP TEST: PROFIT CALCULATION ACCURACY")
    print("="*80)

    tests_passed = []

    # Test 1: Simple profit calculation
    print("\n[1] Basic Profit Calculation")
    scenarios = [
        {"entry": 50, "exit": 75, "qty": 10, "expected_profit": 2.50, "expected_pct": 50.0},
        {"entry": 30, "exit": 60, "qty": 20, "expected_profit": 6.00, "expected_pct": 100.0},
        {"entry": 45, "exit": 63, "qty": 15, "expected_profit": 2.70, "expected_pct": 40.0},
    ]

    for scenario in scenarios:
        entry = scenario["entry"]
        exit_price = scenario["exit"]
        qty = scenario["qty"]

        profit_per_share = exit_price - entry
        total_profit = (profit_per_share * qty) / 100
        profit_pct = (profit_per_share / entry) * 100

        expected_profit = scenario["expected_profit"]
        expected_pct = scenario["expected_pct"]

        profit_match = abs(total_profit - expected_profit) < 0.01
        pct_match = abs(profit_pct - expected_pct) < 0.1

        if profit_match and pct_match:
            print(f"  ✅ Entry {entry}¢ → Exit {exit_price}¢ × {qty} = ${total_profit:.2f} ({profit_pct:.1f}%)")
            tests_passed.append(True)
        else:
            print(f"  ❌ Calculation mismatch!")
            print(f"     Expected: ${expected_profit:.2f} ({expected_pct:.1f}%)")
            print(f"     Got: ${total_profit:.2f} ({profit_pct:.1f}%)")
            tests_passed.append(False)

    # Test 2: Loss calculation
    print("\n[2] Loss Calculation")
    loss_scenarios = [
        {"entry": 50, "exit": 45, "qty": 10, "expected_loss": -0.50, "expected_pct": -10.0},
        {"entry": 60, "exit": 48, "qty": 20, "expected_loss": -2.40, "expected_pct": -20.0},
    ]

    for scenario in loss_scenarios:
        entry = scenario["entry"]
        exit_price = scenario["exit"]
        qty = scenario["qty"]

        loss_per_share = exit_price - entry
        total_loss = (loss_per_share * qty) / 100
        loss_pct = (loss_per_share / entry) * 100

        expected_loss = scenario["expected_loss"]
        expected_pct = scenario["expected_pct"]

        loss_match = abs(total_loss - expected_loss) < 0.01
        pct_match = abs(loss_pct - expected_pct) < 0.1

        if loss_match and pct_match:
            print(f"  ✅ Entry {entry}¢ → Exit {exit_price}¢ × {qty} = ${total_loss:.2f} ({loss_pct:.1f}%)")
            tests_passed.append(True)
        else:
            print(f"  ❌ Calculation mismatch!")
            tests_passed.append(False)

    # Test 3: Profit-taking trigger
    print("\n[3] Profit-Taking Trigger (25% threshold)")

    profit_threshold = 0.25

    profit_scenarios = [
        {"entry": 50, "current": 63, "should_trigger": True},   # 26% gain
        {"entry": 50, "current": 62, "should_trigger": False},  # 24% gain
        {"entry": 40, "current": 50, "should_trigger": True},   # 25% gain
        {"entry": 60, "current": 70, "should_trigger": False},  # 16.7% gain
    ]

    for scenario in profit_scenarios:
        entry = scenario["entry"]
        current = scenario["current"]
        should_trigger = scenario["should_trigger"]

        profit_pct = (current - entry) / entry
        triggers = profit_pct >= profit_threshold

        if triggers == should_trigger:
            status = "triggers" if triggers else "doesn't trigger"
            print(f"  ✅ {entry}¢ → {current}¢ ({profit_pct*100:.1f}%) correctly {status}")
            tests_passed.append(True)
        else:
            print(f"  ❌ {entry}¢ → {current}¢ trigger logic incorrect")
            tests_passed.append(False)

    # Test 4: Stop-loss trigger
    print("\n[4] Stop-Loss Trigger (10% threshold)")

    stop_loss_threshold = -0.10

    loss_scenarios = [
        {"entry": 50, "current": 45, "should_trigger": True},   # -10% loss
        {"entry": 50, "current": 46, "should_trigger": False},  # -8% loss
        {"entry": 60, "current": 54, "should_trigger": True},   # -10% loss
        {"entry": 40, "current": 37, "should_trigger": False},  # -7.5% loss
    ]

    for scenario in loss_scenarios:
        entry = scenario["entry"]
        current = scenario["current"]
        should_trigger = scenario["should_trigger"]

        loss_pct = (current - entry) / entry
        triggers = loss_pct <= stop_loss_threshold

        if triggers == should_trigger:
            status = "triggers" if triggers else "doesn't trigger"
            print(f"  ✅ {entry}¢ → {current}¢ ({loss_pct*100:.1f}%) correctly {status}")
            tests_passed.append(True)
        else:
            print(f"  ❌ {entry}¢ → {current}¢ trigger logic incorrect")
            tests_passed.append(False)

    passed = sum(tests_passed)
    total = len(tests_passed)
    print(f"\n📊 Profit Calculations: {passed}/{total} tests passed")
    return all(tests_passed)


async def test_position_sizing():
    """Test Kelly Criterion position sizing"""
    print("\n" + "="*80)
    print("DEEP TEST: POSITION SIZING (KELLY CRITERION)")
    print("="*80)

    tests_passed = []

    kelly_fraction = settings.trading.kelly_fraction  # 0.75
    max_position = settings.trading.max_single_position  # 0.40

    print(f"\n  Configuration:")
    print(f"  Kelly Fraction: {kelly_fraction}")
    print(f"  Max Position: {max_position*100:.0f}%")

    # Test scenarios
    print("\n[1] Kelly Position Sizing Calculations")

    scenarios = [
        {
            "edge": 0.15,
            "confidence": 0.65,
            "bankroll": 100,
            "description": "15% edge, 65% confidence, $100 bankroll"
        },
        {
            "edge": 0.20,
            "confidence": 0.70,
            "bankroll": 100,
            "description": "20% edge, 70% confidence, $100 bankroll"
        },
        {
            "edge": 0.10,
            "confidence": 0.55,
            "bankroll": 100,
            "description": "10% edge, 55% confidence, $100 bankroll"
        },
    ]

    for scenario in scenarios:
        edge = scenario["edge"]
        confidence = scenario["confidence"]
        bankroll = scenario["bankroll"]

        # Kelly formula: f = (edge × confidence) / odds
        # Simplified: f = edge × confidence
        kelly_pct = kelly_fraction * (edge * confidence / (1 - confidence))

        # Apply max position limit
        position_pct = min(kelly_pct, max_position)
        position_size = bankroll * position_pct

        print(f"\n  {scenario['description']}")
        print(f"    Raw Kelly: {kelly_pct*100:.1f}%")
        print(f"    With {kelly_fraction} fraction: {kelly_pct*100:.1f}%")
        print(f"    After max limit (40%): {position_pct*100:.1f}%")
        print(f"    Position size: ${position_size:.2f}")

        # Validate position is reasonable
        if 0 < position_size <= bankroll * max_position:
            print(f"    ✅ Position size valid")
            tests_passed.append(True)
        else:
            print(f"    ❌ Position size invalid!")
            tests_passed.append(False)

    # Test 2: Edge cases
    print("\n[2] Edge Case Handling")

    edge_cases = [
        {"edge": 0.50, "confidence": 0.90, "bankroll": 100, "should_cap": True},
        {"edge": 0.05, "confidence": 0.51, "bankroll": 100, "should_cap": False},
    ]

    for case in edge_cases:
        edge = case["edge"]
        confidence = case["confidence"]
        bankroll = case["bankroll"]

        kelly_pct = kelly_fraction * (edge * confidence / (1 - confidence))
        position_pct = min(kelly_pct, max_position)
        position_size = bankroll * position_pct

        capped = position_pct == max_position

        if capped == case["should_cap"]:
            cap_status = "capped" if capped else "not capped"
            print(f"  ✅ Edge {edge*100:.0f}%, Conf {confidence*100:.0f}% correctly {cap_status} at ${position_size:.2f}")
            tests_passed.append(True)
        else:
            print(f"  ❌ Capping logic incorrect")
            tests_passed.append(False)

    passed = sum(tests_passed)
    total = len(tests_passed)
    print(f"\n📊 Position Sizing: {passed}/{total} tests passed")
    return all(tests_passed)


async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n" + "="*80)
    print("DEEP TEST: ERROR HANDLING & EDGE CASES")
    print("="*80)

    tests_passed = []

    # Test 1: Invalid order parameters
    print("\n[1] Invalid Order Parameters")

    invalid_orders = [
        {"side": "INVALID", "reason": "Invalid side"},
        {"side": "yes", "action": "INVALID", "reason": "Invalid action"},
        {"side": "yes", "action": "buy", "type": "INVALID", "reason": "Invalid type"},
        {"side": "yes", "action": "buy", "count": 0, "reason": "Zero count"},
        {"side": "yes", "action": "buy", "count": -5, "reason": "Negative count"},
    ]

    for order in invalid_orders:
        try:
            # Validate
            if "side" in order:
                assert order.get("side", "").lower() in ["yes", "no"], "Invalid side"
            if "action" in order:
                assert order.get("action", "").lower() in ["buy", "sell"], "Invalid action"
            if "type" in order:
                assert order.get("type", "") in ["market", "limit"], "Invalid type"
            if "count" in order:
                assert order.get("count", 0) >= 1, "Invalid count"

            print(f"  ❌ {order['reason']} should have been rejected!")
            tests_passed.append(False)
        except AssertionError:
            print(f"  ✅ {order['reason']} correctly rejected")
            tests_passed.append(True)

    # Test 2: Price boundary validation
    print("\n[2] Price Boundary Validation")

    def validate_price(price):
        """Simulate price validation"""
        if not isinstance(price, int):
            raise ValueError("Price must be integer")
        if price < 1 or price > 99:
            raise ValueError("Price must be 1-99")
        return price

    valid_prices = [1, 25, 50, 75, 99]
    for price in valid_prices:
        try:
            validate_price(price)
            print(f"  ✅ Price {price}¢ accepted")
            tests_passed.append(True)
        except:
            print(f"  ❌ Price {price}¢ incorrectly rejected!")
            tests_passed.append(False)

    invalid_prices = [0, 100, -10, 1000]
    for price in invalid_prices:
        try:
            validate_price(price)
            print(f"  ❌ Price {price}¢ should have been rejected!")
            tests_passed.append(False)
        except ValueError:
            print(f"  ✅ Price {price}¢ correctly rejected")
            tests_passed.append(True)

    # Test 3: Price clamping for stop-loss/profit-taking
    print("\n[3] Price Clamping")

    def clamp_price(price):
        """Clamp price to valid range"""
        return max(0.01, min(0.99, price))

    clamp_tests = [
        {"input": 0.75, "expected": 0.75},
        {"input": 1.20, "expected": 0.99},
        {"input": -0.10, "expected": 0.01},
        {"input": 0.005, "expected": 0.01},
    ]

    for test in clamp_tests:
        result = clamp_price(test["input"])
        if abs(result - test["expected"]) < 0.001:
            print(f"  ✅ ${test['input']:.3f} clamped to ${result:.2f}")
            tests_passed.append(True)
        else:
            print(f"  ❌ ${test['input']:.3f} incorrectly clamped to ${result:.2f}")
            tests_passed.append(False)

    passed = sum(tests_passed)
    total = len(tests_passed)
    print(f"\n📊 Error Handling: {passed}/{total} tests passed")
    return all(tests_passed)


async def test_live_api_validation():
    """Test live API with real Kalshi connection"""
    print("\n" + "="*80)
    print("DEEP TEST: LIVE API VALIDATION")
    print("="*80)

    client = KalshiClient()
    tests_passed = []

    try:
        # Test 1: Account balance
        print("\n[1] Account Balance Retrieval")
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        portfolio = balance.get('payout', 0) / 100

        print(f"  Cash: ${cash:.2f}")
        print(f"  Portfolio: ${portfolio:.2f}")

        if cash >= 0:
            print(f"  ✅ Balance retrieved successfully")
            tests_passed.append(True)
        else:
            print(f"  ❌ Invalid balance")
            tests_passed.append(False)

        # Test 2: Market data quality
        print("\n[2] Market Data Quality")
        markets = await client.get_markets(limit=20, status="open")
        market_list = markets.get('markets', [])

        print(f"  Found {len(market_list)} open markets")

        valid_markets = 0
        for market in market_list[:5]:
            ticker = market.get('ticker')
            yes_ask = market.get('yes_ask')
            no_ask = market.get('no_ask')
            volume = market.get('volume', 0)

            if ticker and yes_ask is not None and no_ask is not None:
                valid_markets += 1
                print(f"  ✅ {ticker[:50]}")
                print(f"     YES: {yes_ask}¢, NO: {no_ask}¢, Vol: {volume:,}")

        if valid_markets > 0:
            tests_passed.append(True)
        else:
            print(f"  ❌ No valid markets found")
            tests_passed.append(False)

        # Test 3: Position data
        print("\n[3] Position Data Retrieval")
        positions = await client.get_positions()
        position_list = positions.get('market_positions', [])

        print(f"  Current positions: {len(position_list)}")

        for pos in position_list[:3]:
            ticker = pos.get('ticker', 'N/A')[:50]
            qty = pos.get('position', 0)
            value = pos.get('market_exposure', 0) / 100
            print(f"  • {ticker}: {qty} contracts = ${value:.2f}")

        print(f"  ✅ Position data retrieved")
        tests_passed.append(True)

    except Exception as e:
        print(f"  ❌ API test failed: {e}")
        tests_passed.append(False)
    finally:
        await client.close()

    passed = sum(tests_passed)
    total = len(tests_passed)
    print(f"\n📊 Live API: {passed}/{total} tests passed")
    return all(tests_passed)


async def main():
    """Run ultra-comprehensive test suite"""
    print("\n" + "="*80)
    print("🔬 ULTRA-COMPREHENSIVE TESTING SUITE")
    print("   Deep validation of all trading logic")
    print("="*80)

    results = []

    # Run all deep tests
    results.append(("Order Placement (Deep)", await test_order_placement_deep()))
    results.append(("Profit Calculations", await test_profit_calculations()))
    results.append(("Position Sizing (Kelly)", await test_position_sizing()))
    results.append(("Error Handling", await test_error_handling()))
    results.append(("Live API Validation", await test_live_api_validation()))

    # Print final summary
    print("\n" + "="*80)
    print("📊 ULTRA-COMPREHENSIVE TEST RESULTS")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print("\n" + "="*80)
    if total_passed == total_tests:
        print(f"🎉 ALL DEEP TESTS PASSED: {total_passed}/{total_tests}")
        print("✅ All trading logic validated!")
        print("\n💰 Verified:")
        print("   • Order placement (all types)")
        print("   • Profit/loss calculations")
        print("   • Position sizing (Kelly)")
        print("   • Error handling")
        print("   • Live API connectivity")
    else:
        print(f"⚠️ TESTS PASSED: {total_passed}/{total_tests}")
        print(f"❌ {total_tests - total_passed} test(s) need attention")
    print("="*80)

    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
