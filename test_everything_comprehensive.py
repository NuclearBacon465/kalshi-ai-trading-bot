#!/usr/bin/env python3
"""
Comprehensive Test Suite - Verify ALL Bot Components
Tests everything including: API fixes, dashboards, trading logic, and edge cases.
"""

import asyncio
import sys
import traceback
from datetime import datetime

# Test results tracker
test_results = []

def test_result(name: str, passed: bool, details: str = ""):
    """Track test results."""
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append({
        'name': name,
        'passed': passed,
        'details': details
    })
    print(f"{status} - {name}")
    if details and not passed:
        print(f"      {details}")

async def test_kalshi_api_fixes():
    """Test 1: Verify Kalshi API fixes are in place."""
    print("\n" + "=" * 60)
    print("TEST 1: KALSHI API FIXES")
    print("=" * 60)

    try:
        # Test 1a: Check time_in_force value
        from src.clients.kalshi_client import KalshiClient
        import inspect

        # Read the source code
        source = inspect.getsource(KalshiClient.place_order)

        # Check for correct time_in_force
        if '"good_till_canceled"' in source or "'good_till_canceled'" in source:
            test_result("time_in_force uses official value", True)
        else:
            test_result("time_in_force uses official value", False,
                       "Still using 'gtc' instead of 'good_till_canceled'")

        # Check sell_position_floor is removed
        if 'sell_position_floor' not in source:
            test_result("sell_position_floor removed", True)
        else:
            test_result("sell_position_floor removed", False,
                       "Undocumented parameter still present")

        # Test 1b: Check rate limiting is optimized
        source_full = inspect.getsource(KalshiClient)
        if 'await asyncio.sleep(0.1)' in source_full:
            test_result("Rate limiting optimized to 10 req/sec", True)
        elif 'await asyncio.sleep(0.5)' in source_full:
            test_result("Rate limiting optimized to 10 req/sec", False,
                       "Still using conservative 2 req/sec")
        else:
            test_result("Rate limiting optimized to 10 req/sec", False,
                       "Rate limiting value unclear")

    except Exception as e:
        test_result("Kalshi API fixes check", False, str(e))

async def test_web_dashboard_dependencies():
    """Test 2: Verify web dashboard dependencies."""
    print("\n" + "=" * 60)
    print("TEST 2: WEB DASHBOARD DEPENDENCIES")
    print("=" * 60)

    try:
        # Test Flask
        import flask
        test_result("Flask installed", True, f"Version: {flask.__version__}")
    except ImportError as e:
        test_result("Flask installed", False, "Flask not found in environment")

    try:
        # Test dashboard imports
        from web_dashboard import app
        test_result("Web dashboard imports correctly", True)
    except Exception as e:
        test_result("Web dashboard imports correctly", False, str(e))

    try:
        # Test Beast Mode dashboard
        from beast_mode_dashboard import BeastModeDashboard
        test_result("Beast Mode dashboard imports correctly", True)
    except Exception as e:
        test_result("Beast Mode dashboard imports correctly", False, str(e))

async def test_notifications_system():
    """Test 3: Verify notifications system."""
    print("\n" + "=" * 60)
    print("TEST 3: NOTIFICATIONS SYSTEM")
    print("=" * 60)

    try:
        from src.utils.notifications import get_notifier, TradeNotifier

        notifier = get_notifier()
        test_result("Notification system loads", True)

        # Test notification methods exist
        methods = ['notify_trade_opened', 'notify_trade_closed',
                  'notify_order_placed', 'notify_order_filled']
        for method in methods:
            if hasattr(notifier, method):
                test_result(f"Notifier has {method}", True)
            else:
                test_result(f"Notifier has {method}", False)

    except Exception as e:
        test_result("Notification system", False, str(e))

async def test_edge_filter_optimization():
    """Test 4: Verify ultra-aggressive edge filter."""
    print("\n" + "=" * 60)
    print("TEST 4: EDGE FILTER OPTIMIZATION")
    print("=" * 60)

    try:
        from src.utils.edge_filter import (
            MIN_EDGE_REQUIREMENT,
            HIGH_CONFIDENCE_EDGE,
            MEDIUM_CONFIDENCE_EDGE,
            LOW_CONFIDENCE_EDGE,
            MIN_CONFIDENCE_FOR_TRADE
        )

        # Check ultra-aggressive thresholds
        if MIN_EDGE_REQUIREMENT <= 0.03:
            test_result("MIN_EDGE_REQUIREMENT ultra-aggressive", True,
                       f"{MIN_EDGE_REQUIREMENT:.1%}")
        else:
            test_result("MIN_EDGE_REQUIREMENT ultra-aggressive", False,
                       f"Too conservative: {MIN_EDGE_REQUIREMENT:.1%}")

        if HIGH_CONFIDENCE_EDGE <= 0.02:
            test_result("HIGH_CONFIDENCE_EDGE ultra-aggressive", True,
                       f"{HIGH_CONFIDENCE_EDGE:.1%}")
        else:
            test_result("HIGH_CONFIDENCE_EDGE ultra-aggressive", False,
                       f"Too conservative: {HIGH_CONFIDENCE_EDGE:.1%}")

        if MIN_CONFIDENCE_FOR_TRADE <= 0.45:
            test_result("MIN_CONFIDENCE lowered", True,
                       f"{MIN_CONFIDENCE_FOR_TRADE:.1%}")
        else:
            test_result("MIN_CONFIDENCE lowered", False,
                       f"Too high: {MIN_CONFIDENCE_FOR_TRADE:.1%}")

    except Exception as e:
        test_result("Edge filter optimization", False, str(e))

async def test_trading_execution():
    """Test 5: Verify trading execution logic."""
    print("\n" + "=" * 60)
    print("TEST 5: TRADING EXECUTION LOGIC")
    print("=" * 60)

    try:
        from src.jobs.execute import (
            execute_position,
            place_sell_limit_order,
            place_profit_taking_orders,
            place_stop_loss_orders
        )

        test_result("Execute position function exists", True)
        test_result("Place sell limit order function exists", True)
        test_result("Place profit taking function exists", True)
        test_result("Place stop loss function exists", True)

        # Check price validation in source
        import inspect
        source = inspect.getsource(place_profit_taking_orders)

        if 'max(0.01, min(0.99' in source:
            test_result("Profit-taking has price clamping", True)
        else:
            test_result("Profit-taking has price clamping", False,
                       "Missing 1¢-99¢ validation")

        source_sl = inspect.getsource(place_stop_loss_orders)
        if 'max(0.01, min(0.99' in source_sl:
            test_result("Stop-loss has price clamping", True)
        else:
            test_result("Stop-loss has price clamping", False,
                       "Missing 1¢-99¢ validation")

    except Exception as e:
        test_result("Trading execution logic", False, str(e))

async def test_database_operations():
    """Test 6: Verify database operations."""
    print("\n" + "=" * 60)
    print("TEST 6: DATABASE OPERATIONS")
    print("=" * 60)

    try:
        from src.utils.database import DatabaseManager

        db = DatabaseManager()
        await db.initialize()
        test_result("Database initializes", True)

        # Check for critical methods
        methods = [
            'get_open_positions',
            'get_open_live_positions',
            'get_active_markets',
            'get_eligible_markets',
            'update_position_to_live',
            'update_position_status'
        ]

        for method in methods:
            if hasattr(db, method):
                test_result(f"Database has {method}", True)
            else:
                test_result(f"Database has {method}", False)

    except Exception as e:
        test_result("Database operations", False, str(e))

async def test_portfolio_optimizer():
    """Test 7: Verify portfolio optimizer."""
    print("\n" + "=" * 60)
    print("TEST 7: PORTFOLIO OPTIMIZER")
    print("=" * 60)

    try:
        from src.strategies.portfolio_optimization import AdvancedPortfolioOptimizer
        from src.utils.database import DatabaseManager
        from src.clients.kalshi_client import KalshiClient
        from src.clients.xai_client import XAIClient

        db = DatabaseManager()
        await db.initialize()
        kalshi = KalshiClient()
        xai = XAIClient()

        # Test initialization with valid parameters
        optimizer = AdvancedPortfolioOptimizer(db, kalshi, xai)
        test_result("Portfolio optimizer initializes", True)

        # Test that None parameters are rejected
        try:
            bad_optimizer = AdvancedPortfolioOptimizer(None, kalshi, xai)
            test_result("Rejects None database parameter", False,
                       "Should raise ValueError for None")
        except ValueError:
            test_result("Rejects None database parameter", True)
        except Exception as e:
            test_result("Rejects None database parameter", False, str(e))

        await kalshi.close()
        await xai.close()

    except Exception as e:
        test_result("Portfolio optimizer", False, str(e))

async def test_api_authentication():
    """Test 8: Verify API authentication works."""
    print("\n" + "=" * 60)
    print("TEST 8: API AUTHENTICATION")
    print("=" * 60)

    try:
        from src.clients.kalshi_client import KalshiClient
        from src.clients.xai_client import XAIClient

        # Test Kalshi client
        kalshi = KalshiClient()
        test_result("Kalshi client initializes", True)

        try:
            balance = await kalshi.get_balance()
            dollars = balance.get('balance', 0) / 100
            test_result("Kalshi API authentication works", True,
                       f"Balance: ${dollars:.2f}")
        except Exception as e:
            test_result("Kalshi API authentication works", False, str(e))
        finally:
            await kalshi.close()

        # Test xAI client
        xai = XAIClient()
        test_result("xAI client initializes", True)
        await xai.close()

    except Exception as e:
        test_result("API authentication", False, str(e))

async def test_market_data_processing():
    """Test 9: Verify market data processing."""
    print("\n" + "=" * 60)
    print("TEST 9: MARKET DATA PROCESSING")
    print("=" * 60)

    try:
        from src.jobs.ingest import run_ingestion
        from src.utils.database import DatabaseManager

        db = DatabaseManager()
        await db.initialize()

        market_queue = asyncio.Queue()

        # Run ingestion once
        await run_ingestion(db, market_queue)
        test_result("Market ingestion runs", True)

        # Check if markets were ingested
        markets = await db.get_active_markets()
        if markets and len(markets) > 0:
            test_result("Markets ingested into database", True,
                       f"{len(markets)} markets")
        else:
            test_result("Markets ingested into database", False,
                       "No markets found")

    except Exception as e:
        test_result("Market data processing", False, str(e))

async def test_unified_trading_system():
    """Test 10: Verify unified trading system."""
    print("\n" + "=" * 60)
    print("TEST 10: UNIFIED TRADING SYSTEM")
    print("=" * 60)

    try:
        from src.strategies.unified_trading_system import (
            UnifiedAdvancedTradingSystem,
            TradingSystemConfig
        )
        from src.utils.database import DatabaseManager
        from src.clients.kalshi_client import KalshiClient
        from src.clients.xai_client import XAIClient

        db = DatabaseManager()
        await db.initialize()
        kalshi = KalshiClient()
        xai = XAIClient()

        system = UnifiedAdvancedTradingSystem(db, kalshi, xai)
        test_result("Unified trading system initializes", True)

        # Check key components
        if hasattr(system, 'market_maker'):
            test_result("Has market maker component", True)
        else:
            test_result("Has market maker component", False)

        if hasattr(system, 'portfolio_optimizer'):
            test_result("Has portfolio optimizer component", True)
        else:
            test_result("Has portfolio optimizer component", False)

        await kalshi.close()
        await xai.close()

    except Exception as e:
        test_result("Unified trading system", False, str(e))

def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total = len(test_results)
    passed = sum(1 for r in test_results if r['passed'])
    failed = total - passed

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if failed > 0:
        print("\n🔴 FAILED TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"   - {result['name']}")
                if result['details']:
                    print(f"     {result['details']}")

    print("\n" + "=" * 60)

    if passed == total:
        print("🎉 ALL TESTS PASSED - BOT IS READY!")
        print("=" * 60)
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW ABOVE")
        print("=" * 60)
        return 1

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 COMPREHENSIVE BOT TEST SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run all tests
        await test_kalshi_api_fixes()
        await test_web_dashboard_dependencies()
        await test_notifications_system()
        await test_edge_filter_optimization()
        await test_trading_execution()
        await test_database_operations()
        await test_portfolio_optimizer()
        await test_api_authentication()
        await test_market_data_processing()
        await test_unified_trading_system()

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        return 1

    return print_summary()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
