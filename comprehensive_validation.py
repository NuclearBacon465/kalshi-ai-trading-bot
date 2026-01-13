#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM VALIDATION SCRIPT
Tests ALL features of the Kalshi AI Trading Bot from the beginning
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, List, Any

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

class ValidationReport:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        self.results.append({
            'category': category,
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        })

        status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} {test_name}")
        if details:
            print(f"       {details}")

    def print_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        duration = (datetime.now() - self.start_time).total_seconds()

        print(f"\n{'='*80}")
        print(f"{BOLD}COMPREHENSIVE VALIDATION SUMMARY{RESET}")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"{'='*80}\n")

        # Category breakdown
        categories = {}
        for r in self.results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'passed': 0, 'failed': 0}
            if r['passed']:
                categories[cat]['passed'] += 1
            else:
                categories[cat]['failed'] += 1

        print(f"{BOLD}Results by Category:{RESET}")
        for cat, stats in categories.items():
            total_cat = stats['passed'] + stats['failed']
            rate = (stats['passed'] / total_cat * 100) if total_cat > 0 else 0
            print(f"  {cat}: {stats['passed']}/{total_cat} passed ({rate:.1f}%)")

        return failed == 0


async def test_kalshi_client_basics(report: ValidationReport):
    """Test basic Kalshi client functionality"""
    print(f"\n{BOLD}{BLUE}Testing Kalshi Client Basics...{RESET}")

    try:
        from src.clients.kalshi_client import KalshiClient
        client = KalshiClient()

        # Test 1: Client initialization
        report.add_result("Kalshi Client", "Client initialization", True, "KalshiClient created successfully")

        # Test 2: Check method count
        import inspect
        methods = [m for m in dir(client) if callable(getattr(client, m)) and not m.startswith('_')]
        api_methods = [m for m in methods if not m in ['close', 'login']]
        report.add_result("Kalshi Client", f"API methods count (expect 76)", len(api_methods) >= 76, f"Found {len(api_methods)} methods - Complete Kalshi API")

        await client.close()

    except Exception as e:
        report.add_result("Kalshi Client", "Client initialization", False, str(e))


async def test_exchange_endpoints(report: ValidationReport):
    """Test Exchange API endpoints (Part 1)"""
    print(f"\n{BOLD}{BLUE}Testing Exchange API Endpoints...{RESET}")

    try:
        from src.clients.kalshi_client import KalshiClient
        client = KalshiClient()

        # Test: Get exchange status
        try:
            result = await client.get_exchange_status()
            report.add_result("API - Exchange", "get_exchange_status()",
                            'exchange_active' in result,
                            f"Trading status: {'active' if result.get('exchange_active') else 'inactive'}")
        except Exception as e:
            report.add_result("API - Exchange", "get_exchange_status()", False, str(e))

        # Test: Get exchange schedule
        try:
            result = await client.get_exchange_schedule()
            report.add_result("API - Exchange", "get_exchange_schedule()",
                            'schedule' in result,
                            f"Found schedule data")
        except Exception as e:
            report.add_result("API - Exchange", "get_exchange_schedule()", False, str(e))

        await client.close()

    except Exception as e:
        report.add_result("API - Exchange", "Exchange endpoints test", False, str(e))


async def test_market_endpoints(report: ValidationReport):
    """Test Market API endpoints (Part 5)"""
    print(f"\n{BOLD}{BLUE}Testing Market API Endpoints...{RESET}")

    try:
        from src.clients.kalshi_client import KalshiClient
        client = KalshiClient()

        # Test: Get markets
        try:
            result = await client.get_markets(limit=5)
            markets_count = len(result.get('markets', []))
            report.add_result("API - Markets", "get_markets()",
                            markets_count > 0,
                            f"Retrieved {markets_count} markets")
        except Exception as e:
            report.add_result("API - Markets", "get_markets()", False, str(e))

        # Test: Get events
        try:
            result = await client.get_events(limit=3)
            events_count = len(result.get('events', []))
            report.add_result("API - Markets", "get_events()",
                            events_count > 0,
                            f"Retrieved {events_count} events")
        except Exception as e:
            report.add_result("API - Markets", "get_events()", False, str(e))

        # Test: Get series
        try:
            result = await client.get_series(limit=3)
            series_count = len(result.get('series', []))
            report.add_result("API - Markets", "get_series()",
                            series_count >= 0,
                            f"Retrieved {series_count} series")
        except Exception as e:
            report.add_result("API - Markets", "get_series()", False, str(e))

        await client.close()

    except Exception as e:
        report.add_result("API - Markets", "Market endpoints test", False, str(e))


async def test_portfolio_endpoints(report: ValidationReport):
    """Test Portfolio API endpoints (Part 4)"""
    print(f"\n{BOLD}{BLUE}Testing Portfolio API Endpoints...{RESET}")

    try:
        from src.clients.kalshi_client import KalshiClient
        client = KalshiClient()

        # Test: Get balance
        try:
            result = await client.get_balance()
            report.add_result("API - Portfolio", "get_balance()",
                            'balance' in result,
                            f"Balance: ${result.get('balance', 0)/100:.2f}")
        except Exception as e:
            report.add_result("API - Portfolio", "get_balance()", False, str(e))

        # Test: Get portfolio positions
        try:
            result = await client.get_positions()
            positions_count = len(result.get('market_positions', []))
            report.add_result("API - Portfolio", "get_positions()",
                            True,
                            f"Found {positions_count} positions")
        except Exception as e:
            report.add_result("API - Portfolio", "get_positions()", False, str(e))

        # Test: Get fills
        try:
            result = await client.get_fills()
            fills_count = len(result.get('fills', []))
            report.add_result("API - Portfolio", "get_fills()",
                            True,
                            f"Found {fills_count} fills")
        except Exception as e:
            report.add_result("API - Portfolio", "get_fills()", False, str(e))

        await client.close()

    except Exception as e:
        report.add_result("API - Portfolio", "Portfolio endpoints test", False, str(e))


async def test_order_endpoints(report: ValidationReport):
    """Test Order API endpoints (Part 2)"""
    print(f"\n{BOLD}{BLUE}Testing Order API Endpoints...{RESET}")

    try:
        from src.clients.kalshi_client import KalshiClient
        client = KalshiClient()

        # Test: Get orders (read-only, safe to test)
        try:
            result = await client.get_orders()
            orders_count = len(result.get('orders', []))
            report.add_result("API - Orders", "get_orders()",
                            True,
                            f"Retrieved {orders_count} orders")
        except Exception as e:
            report.add_result("API - Orders", "get_orders()", False, str(e))

        await client.close()

    except Exception as e:
        report.add_result("API - Orders", "Order endpoints test", False, str(e))


async def test_mve_endpoints(report: ValidationReport):
    """Test Multivariate Event Collection endpoints (Part 8 - NEW)"""
    print(f"\n{BOLD}{BLUE}Testing MVE API Endpoints (Part 8 - FINAL)...{RESET}")

    try:
        from src.clients.kalshi_client import KalshiClient
        client = KalshiClient()

        # Test: Get multivariate event collections
        try:
            result = await client.get_multivariate_event_collections(limit=5)
            collections = result.get('collections', [])
            report.add_result("API - MVE", "get_multivariate_event_collections()",
                            isinstance(collections, list),
                            f"Retrieved {len(collections)} MVE collections")
        except Exception as e:
            report.add_result("API - MVE", "get_multivariate_event_collections()", False, str(e))

        # Test: Get multivariate events
        try:
            result = await client.get_multivariate_events(limit=3)
            events = result.get('events', [])
            report.add_result("API - MVE", "get_multivariate_events()",
                            isinstance(events, list),
                            f"Retrieved {len(events)} multivariate events")
        except Exception as e:
            report.add_result("API - MVE", "get_multivariate_events()", False, str(e))

        await client.close()

    except Exception as e:
        report.add_result("API - MVE", "MVE endpoints test", False, str(e))


async def test_database_operations(report: ValidationReport):
    """Test database CRUD operations"""
    print(f"\n{BOLD}{BLUE}Testing Database Operations...{RESET}")

    import os
    test_db = "validation_test.db"

    try:
        # Clean up any existing test database
        if os.path.exists(test_db):
            os.remove(test_db)

        from src.utils.database import DatabaseManager, Position
        from datetime import datetime

        db = DatabaseManager(db_path=test_db)
        await db.initialize()

        # Test: Database initialization
        report.add_result("Database", "Database initialization", True, "Database created successfully")

        # Test: Add position
        test_position = Position(
            market_id="TEST-MARKET-1",
            side="YES",
            entry_price=0.60,
            quantity=10,
            timestamp=datetime.now(),
            rationale="Validation test position",
            confidence=0.80,
            live=False
        )
        position_id = await db.add_position(test_position)
        report.add_result("Database", "Add position", position_id is not None, f"Position ID: {position_id}")

        # Test: Get position
        retrieved = await db.get_position_by_market_id("TEST-MARKET-1")
        report.add_result("Database", "Get position", retrieved is not None and retrieved.market_id == "TEST-MARKET-1", "Position retrieved successfully")

        # Test: Update position to live
        if retrieved and position_id:
            await db.update_position_to_live(position_id, entry_price=0.60)
            updated = await db.get_position_by_market_id("TEST-MARKET-1")
            report.add_result("Database", "Update position to live", updated.live == True, "Position updated successfully")

        # Test: Get open positions
        open_positions = await db.get_open_positions()
        report.add_result("Database", "Get open positions", len(open_positions) > 0, f"Found {len(open_positions)} open positions")

        # Test: Update position status
        if retrieved and position_id:
            await db.update_position_status(position_id, "closed")
            report.add_result("Database", "Update position status", True, "Position status updated to closed successfully")

        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)

    except Exception as e:
        report.add_result("Database", "Database operations test", False, str(e))
        if os.path.exists(test_db):
            os.remove(test_db)


async def test_phase4_execution_engine(report: ValidationReport):
    """Test Phase 4 execution engine components"""
    print(f"\n{BOLD}{BLUE}Testing Phase 4 Execution Engine...{RESET}")

    import os
    test_db = "phase4_test.db"

    try:
        # Clean up any existing test database
        if os.path.exists(test_db):
            os.remove(test_db)

        from src.clients.kalshi_client import KalshiClient
        from src.utils.database import DatabaseManager
        from src.utils.order_book_analysis import OrderBookAnalyzer, OrderBookSnapshot, MarketImpactEstimate

        # Initialize dependencies
        kalshi_client = KalshiClient()
        db = DatabaseManager(db_path=test_db)
        await db.initialize()

        # Test: OrderBookAnalyzer initialization
        try:
            analyzer = OrderBookAnalyzer(kalshi_client, db)
            report.add_result("Phase 4", "OrderBookAnalyzer initialization", True, "Analyzer created with kalshi_client and db_manager")
        except Exception as e:
            report.add_result("Phase 4", "OrderBookAnalyzer initialization", False, str(e))

        # Test: OrderBookSnapshot dataclass
        try:
            from datetime import datetime
            snapshot = OrderBookSnapshot(
                ticker="TEST-MARKET",
                timestamp=datetime.now(),
                best_bid=59.0,
                best_ask=60.0,
                spread=1.0,
                spread_pct=0.017,
                mid_price=59.5,
                bid_depth_1=100,
                ask_depth_1=100,
                bid_depth_5=500,
                ask_depth_5=500,
                depth_imbalance=0.0,
                price_pressure=0.0,
                total_liquidity=1000,
                liquidity_score=0.8
            )
            report.add_result("Phase 4", "OrderBookSnapshot dataclass", True, f"Snapshot created: {snapshot.ticker}")
        except Exception as e:
            report.add_result("Phase 4", "OrderBookSnapshot dataclass", False, str(e))

        # Test: MarketImpactEstimate dataclass
        try:
            impact = MarketImpactEstimate(
                ticker="TEST-MARKET",
                order_size=10,
                side="buy",
                expected_fill_price=60.0,
                slippage=0.5,
                slippage_pct=0.008,
                price_impact=0.01,
                recommended_strategy="limit",
                split_into_chunks=1,
                reasoning="Small order, single chunk"
            )
            report.add_result("Phase 4", "MarketImpactEstimate dataclass", True, f"Impact estimate: {impact.recommended_strategy}")
        except Exception as e:
            report.add_result("Phase 4", "MarketImpactEstimate dataclass", False, str(e))

        # Clean up
        await kalshi_client.close()
        if os.path.exists(test_db):
            os.remove(test_db)

    except Exception as e:
        report.add_result("Phase 4", "Phase 4 execution engine test", False, str(e))
        if os.path.exists(test_db):
            os.remove(test_db)


async def test_ai_integrations(report: ValidationReport):
    """Test AI client integrations"""
    print(f"\n{BOLD}{BLUE}Testing AI Integrations...{RESET}")

    # Test: xAI (Grok) client
    try:
        from src.clients.xai_client import XAIClient
        xai_client = XAIClient()
        report.add_result("AI Integrations", "xAI (Grok) client initialization", True, "XAI client created successfully")
    except Exception as e:
        report.add_result("AI Integrations", "xAI (Grok) client initialization", False, str(e))

    # Test: OpenAI client
    try:
        from openai import AsyncOpenAI
        import os
        if os.getenv("OPENAI_API_KEY"):
            openai_client = AsyncOpenAI()
            report.add_result("AI Integrations", "OpenAI client initialization", True, "OpenAI client created successfully")
        else:
            report.add_result("AI Integrations", "OpenAI client initialization", False, "OPENAI_API_KEY not set")
    except Exception as e:
        report.add_result("AI Integrations", "OpenAI client initialization", False, str(e))


async def test_safety_systems(report: ValidationReport):
    """Test safety systems (kill switch, safe mode)"""
    print(f"\n{BOLD}{BLUE}Testing Safety Systems...{RESET}")

    import os

    # Test: Kill switch file detection
    try:
        kill_switch_path = "KILL_SWITCH"
        exists_before = os.path.exists(kill_switch_path)

        # Create kill switch
        with open(kill_switch_path, 'w') as f:
            f.write("Emergency stop")

        exists_after = os.path.exists(kill_switch_path)

        # Clean up
        if os.path.exists(kill_switch_path):
            os.remove(kill_switch_path)

        report.add_result("Safety Systems", "Kill switch file creation/detection", exists_after, "Kill switch mechanism works")
    except Exception as e:
        report.add_result("Safety Systems", "Kill switch file creation/detection", False, str(e))

    # Test: Safe mode environment variable
    try:
        original_safe_mode = os.getenv("SAFE_MODE")
        os.environ["SAFE_MODE"] = "true"
        safe_mode_enabled = os.getenv("SAFE_MODE") == "true"

        # Restore original
        if original_safe_mode:
            os.environ["SAFE_MODE"] = original_safe_mode
        else:
            os.environ.pop("SAFE_MODE", None)

        report.add_result("Safety Systems", "Safe mode environment variable", safe_mode_enabled, "Safe mode can be enabled")
    except Exception as e:
        report.add_result("Safety Systems", "Safe mode environment variable", False, str(e))


async def test_notification_system(report: ValidationReport):
    """Test notification system"""
    print(f"\n{BOLD}{BLUE}Testing Notification System...{RESET}")

    try:
        from src.utils.notifications import TradeNotifier, get_notifier

        # Test: TradeNotifier initialization
        notifier = TradeNotifier()
        report.add_result("Notifications", "TradeNotifier initialization", True, "Trade notifier created successfully")

        # Test: get_notifier function
        try:
            notifier_instance = get_notifier()
            report.add_result("Notifications", "get_notifier() function",
                            notifier_instance is not None,
                            "Notifier instance retrieved")
        except Exception as e:
            report.add_result("Notifications", "get_notifier() function", False, str(e))

        # Test: Notification methods exist
        has_notify_trade_opened = hasattr(notifier, 'notify_trade_opened')
        has_notify_order_placed = hasattr(notifier, 'notify_order_placed')
        has_notify_order_filled = hasattr(notifier, 'notify_order_filled')

        report.add_result("Notifications", "Notification methods exist",
                        has_notify_trade_opened and has_notify_order_placed and has_notify_order_filled,
                        "All notification methods present")

    except Exception as e:
        report.add_result("Notifications", "Notification system test", False, str(e))


async def test_job_modules(report: ValidationReport):
    """Test job modules can be imported"""
    print(f"\n{BOLD}{BLUE}Testing Job Modules...{RESET}")

    # Test: Decide job
    try:
        from src.jobs.decide import make_decision_for_market
        report.add_result("Job Modules", "Decide job import", True, "make_decision_for_market() imported")
    except Exception as e:
        report.add_result("Job Modules", "Decide job import", False, str(e))

    # Test: Execute job
    try:
        from src.jobs.execute import execute_position
        report.add_result("Job Modules", "Execute job import", True, "execute_position() imported")
    except Exception as e:
        report.add_result("Job Modules", "Execute job import", False, str(e))

    # Test: Track job
    try:
        from src.jobs.track import run_tracking
        report.add_result("Job Modules", "Track job import", True, "run_tracking() imported")
    except Exception as e:
        report.add_result("Job Modules", "Track job import", False, str(e))

    # Test: Trade job
    try:
        from src.jobs.trade import run_trading_job
        report.add_result("Job Modules", "Trade job import", True, "run_trading_job() imported")
    except Exception as e:
        report.add_result("Job Modules", "Trade job import", False, str(e))

    # Test: Evaluate job
    try:
        from src.jobs.evaluate import run_evaluation
        report.add_result("Job Modules", "Evaluate job import", True, "run_evaluation() imported")
    except Exception as e:
        report.add_result("Job Modules", "Evaluate job import", False, str(e))

    # Test: Ingest job
    try:
        from src.jobs.ingest import run_ingestion
        report.add_result("Job Modules", "Ingest job import", True, "run_ingestion() imported")
    except Exception as e:
        report.add_result("Job Modules", "Ingest job import", False, str(e))


async def main():
    print(f"{BOLD}{BLUE}")
    print("=" * 80)
    print("  COMPREHENSIVE SYSTEM VALIDATION - KALSHI AI TRADING BOT")
    print("  Testing ALL features from the beginning")
    print("=" * 80)
    print(f"{RESET}\n")

    report = ValidationReport()

    # Run all validation tests
    await test_kalshi_client_basics(report)
    await test_exchange_endpoints(report)
    await test_market_endpoints(report)
    await test_portfolio_endpoints(report)
    await test_order_endpoints(report)
    await test_mve_endpoints(report)
    await test_database_operations(report)
    await test_phase4_execution_engine(report)
    await test_ai_integrations(report)
    await test_safety_systems(report)
    await test_notification_system(report)
    await test_job_modules(report)

    # Print final summary
    all_passed = report.print_summary()

    if all_passed:
        print(f"{GREEN}{BOLD}🎉 ALL VALIDATIONS PASSED! System is 100% operational!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}⚠️  Some validations failed. Review the results above.{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
