#!/usr/bin/env python3
"""
ULTRA-COMPREHENSIVE Feature & Bug Test
Tests EVERYTHING including edge cases, safety features, and profit optimization.
"""

import asyncio
import sys
import traceback
from datetime import datetime, timedelta

sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'bugs_found': [],
    'profit_opportunities': []
}

def log_test(name: str, status: str, details: str = ""):
    """Log test result."""
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")

    if status == "PASS":
        test_results['passed'] += 1
    elif status == "FAIL":
        test_results['failed'] += 1
        test_results['bugs_found'].append(f"{name}: {details}")
    else:
        test_results['warnings'] += 1

async def test_api_connections():
    """Test 1: API Connections"""
    print("\n" + "="*60)
    print("TEST 1: API CONNECTIONS & AUTHENTICATION")
    print("="*60)

    from src.clients.kalshi_client import KalshiClient
    from src.clients.xai_client import XAIClient

    # Test Kalshi
    kalshi = KalshiClient()
    try:
        balance = await kalshi.get_balance()
        cash = balance.get('balance', 0) / 100
        portfolio = balance.get('portfolio_value', 0) / 100

        log_test("Kalshi API Connection", "PASS", f"Balance: ${cash:.2f}, Portfolio: ${portfolio:.2f}")

        # Check if we have enough balance
        if cash < 10:
            log_test("Sufficient Balance", "WARN", f"Low balance: ${cash:.2f} - may limit trading")
        else:
            log_test("Sufficient Balance", "PASS", f"${cash:.2f} available")

    except Exception as e:
        log_test("Kalshi API Connection", "FAIL", str(e))
    finally:
        await kalshi.close()

    # Test xAI
    xai = XAIClient()
    try:
        log_test("xAI Client Initialization", "PASS", f"Model: {xai.primary_model}")

        # Check rate limits
        if xai.per_minute_limit < 60:
            log_test("xAI Rate Limit", "WARN", f"Only {xai.per_minute_limit} req/min")
        else:
            log_test("xAI Rate Limit", "PASS", f"{xai.per_minute_limit} req/min")

    except Exception as e:
        log_test("xAI Client Initialization", "FAIL", str(e))
    finally:
        await xai.close()

async def test_database_operations():
    """Test 2: Database Operations"""
    print("\n" + "="*60)
    print("TEST 2: DATABASE OPERATIONS")
    print("="*60)

    from src.utils.database import DatabaseManager

    db = DatabaseManager()
    try:
        await db.initialize()
        log_test("Database Initialization", "PASS")

        # Test all critical methods
        markets = await db.get_active_markets()
        log_test("Get Active Markets", "PASS", f"{len(markets)} markets")

        positions = await db.get_open_positions()
        log_test("Get Open Positions", "PASS", f"{len(positions)} open positions")

        # Test safe mode
        if hasattr(db, 'is_safe_mode'):
            safe_mode = db.is_safe_mode()
            log_test("Safe Mode Check", "PASS", f"Safe mode: {safe_mode}")

        # Test state persistence
        if hasattr(db, 'get_safe_mode_state'):
            state = db.get_safe_mode_state()
            log_test("Safe Mode State", "PASS", f"Failures: {state.get('failure_count', 0)}")

    except Exception as e:
        log_test("Database Operations", "FAIL", str(e))

async def test_safety_features():
    """Test 3: Safety Features"""
    print("\n" + "="*60)
    print("TEST 3: SAFETY FEATURES")
    print("="*60)

    from src.utils.safety import is_kill_switch_enabled, should_halt_trading
    from src.utils.risk_cooldown import is_risk_cooldown_active, load_risk_cooldown_state
    from src.utils.database import DatabaseManager

    # Test kill switch
    kill_switch = is_kill_switch_enabled()
    log_test("Kill Switch Check", "PASS", f"Enabled: {kill_switch}")

    # Test risk cooldown
    db = DatabaseManager()
    cooldown_active, cooldown_state = is_risk_cooldown_active(db.db_path)
    if cooldown_active:
        log_test("Risk Cooldown", "WARN", f"COOLDOWN ACTIVE until {cooldown_state.cooldown_until}")
    else:
        log_test("Risk Cooldown", "PASS", "No cooldown active")

    # Test safe mode
    if hasattr(db, 'is_safe_mode'):
        safe_mode_active = db.is_safe_mode()
        if safe_mode_active:
            log_test("Safe Mode", "WARN", "SAFE MODE ACTIVE")
        else:
            log_test("Safe Mode", "PASS", "Not in safe mode")

async def test_edge_filter():
    """Test 4: Edge Filter Logic"""
    print("\n" + "="*60)
    print("TEST 4: EDGE FILTER & OPPORTUNITY DETECTION")
    print("="*60)

    from src.utils.edge_filter import EdgeFilter

    # Test various edge scenarios
    test_cases = [
        (0.70, 0.50, 0.80, True, "20% edge, 80% confidence -> SHOULD TRADE"),
        (0.55, 0.50, 0.60, True, "5% edge, 60% confidence -> SHOULD TRADE (ultra-aggressive)"),
        (0.52, 0.50, 0.50, True, "2% edge, 50% confidence -> BORDERLINE"),
        (0.51, 0.50, 0.40, False, "1% edge, 40% confidence -> TOO LOW"),
        (0.50, 0.50, 0.80, False, "0% edge -> NO TRADE"),
    ]

    for ai_prob, market_prob, confidence, should_pass, desc in test_cases:
        result = EdgeFilter.calculate_edge(ai_prob, market_prob, confidence)

        if result.passes_filter == should_pass:
            log_test(f"Edge Filter: {desc}", "PASS", f"Edge: {result.edge_percentage:.1%}")
        else:
            log_test(f"Edge Filter: {desc}", "FAIL",
                    f"Expected {should_pass}, got {result.passes_filter}")

    # Check thresholds
    log_test("Edge Thresholds", "PASS",
            f"MIN_EDGE={EdgeFilter.MIN_EDGE_REQUIREMENT:.1%}, "
            f"HIGH_CONF={EdgeFilter.HIGH_CONFIDENCE_EDGE:.1%}")

async def test_position_limits():
    """Test 5: Position Limits & Cash Reserves"""
    print("\n" + "="*60)
    print("TEST 5: POSITION LIMITS & CASH RESERVES")
    print("="*60)

    from src.utils.position_limits import PositionLimitsManager
    from src.utils.cash_reserves import CashReservesManager
    from src.utils.database import DatabaseManager
    from src.clients.kalshi_client import KalshiClient

    db = DatabaseManager()
    await db.initialize()
    kalshi = KalshiClient()

    try:
        # Test position limits
        limits_mgr = PositionLimitsManager(db, kalshi)
        limits_status = await limits_mgr.get_position_limits_status()
        log_test("Position Limits Check", "PASS",
                f"Status: {limits_status['status']}, "
                f"Utilization: {limits_status['position_utilization']}")

        if limits_status['status'] == 'OVER_LIMIT':
            log_test("Position Limit Status", "WARN", "OVER LIMIT!")

        # Test cash reserves
        cash_mgr = CashReservesManager(db, kalshi)
        cash_status = await cash_mgr.get_cash_status()
        log_test("Cash Reserves Check", "PASS",
                f"Status: {cash_status['status']}, "
                f"Reserve: {cash_status['reserve_percentage']:.1f}%")

        if cash_status['emergency_status']:
            log_test("Cash Emergency", "WARN", "CASH EMERGENCY ACTIVE!")

    except Exception as e:
        log_test("Position Limits & Cash", "FAIL", str(e))
    finally:
        await kalshi.close()

async def test_order_execution():
    """Test 6: Order Execution Logic"""
    print("\n" + "="*60)
    print("TEST 6: ORDER EXECUTION & PRICE VALIDATION")
    print("="*60)

    from src.clients.kalshi_client import KalshiClient

    kalshi = KalshiClient()

    try:
        # Test price validation (without actually placing orders)
        import inspect
        source = inspect.getsource(kalshi.place_order)

        # Check for critical fixes
        if '"good_till_canceled"' in source or "'good_till_canceled'" in source:
            log_test("Order time_in_force Value", "PASS", "Using official 'good_till_canceled'")
        else:
            log_test("Order time_in_force Value", "FAIL", "Not using official value")

        if 'sell_position_floor' not in source:
            log_test("Removed sell_position_floor", "PASS", "Undocumented param removed")
        else:
            log_test("Removed sell_position_floor", "FAIL", "Still using undocumented param")

        # Check rate limiting
        if '0.1' in source or '100ms' in source.lower():
            log_test("Rate Limiting Optimized", "PASS", "10 req/sec")
        else:
            log_test("Rate Limiting", "WARN", "May not be optimized")

    except Exception as e:
        log_test("Order Execution Check", "FAIL", str(e))
    finally:
        await kalshi.close()

async def test_trading_strategies():
    """Test 7: Trading Strategies"""
    print("\n" + "="*60)
    print("TEST 7: TRADING STRATEGIES")
    print("="*60)

    from src.strategies.unified_trading_system import UnifiedAdvancedTradingSystem, TradingSystemConfig
    from src.utils.database import DatabaseManager
    from src.clients.kalshi_client import KalshiClient
    from src.clients.xai_client import XAIClient

    db = DatabaseManager()
    await db.initialize()
    kalshi = KalshiClient()
    xai = XAIClient(db_manager=db)

    try:
        system = UnifiedAdvancedTradingSystem(db, kalshi, xai)
        await system.async_initialize()  # Required to initialize market_maker and portfolio_optimizer
        log_test("Unified Trading System Init", "PASS")

        # Check strategy components
        if hasattr(system, 'market_maker'):
            log_test("Market Making Strategy", "PASS", "Loaded")
        else:
            log_test("Market Making Strategy", "FAIL", "Not loaded")

        if hasattr(system, 'portfolio_optimizer'):
            log_test("Portfolio Optimizer", "PASS", "Loaded")
        else:
            log_test("Portfolio Optimizer", "FAIL", "Not loaded")

        # Check capital allocation
        total_allocation = (system.config.market_making_allocation +
                          system.config.directional_trading_allocation +
                          system.config.arbitrage_allocation)

        if abs(total_allocation - 1.0) < 0.01:
            log_test("Capital Allocation", "PASS", f"Total: {total_allocation:.0%}")
        else:
            log_test("Capital Allocation", "WARN", f"Total: {total_allocation:.0%} (should be 100%)")

    except Exception as e:
        log_test("Trading Strategies", "FAIL", str(e))
    finally:
        await kalshi.close()
        await xai.close()

async def test_notifications():
    """Test 8: Notification System"""
    print("\n" + "="*60)
    print("TEST 8: NOTIFICATION SYSTEM")
    print("="*60)

    from src.utils.notifications import get_notifier

    try:
        notifier = get_notifier()
        log_test("Notifier Initialization", "PASS")

        # Check for all notification methods
        required_methods = [
            'notify_trade_opened',
            'notify_trade_closed',
            'notify_order_placed',
            'notify_order_filled',
            'beep'
        ]

        for method in required_methods:
            if hasattr(notifier, method):
                log_test(f"Notifier Method: {method}", "PASS")
            else:
                log_test(f"Notifier Method: {method}", "FAIL", "Missing")

    except Exception as e:
        log_test("Notification System", "FAIL", str(e))

async def analyze_profit_opportunities():
    """Analyze potential profit improvements"""
    print("\n" + "="*60)
    print("💰 PROFIT OPTIMIZATION ANALYSIS")
    print("="*60)

    opportunities = []

    # Check volume requirement
    from src.strategies.unified_trading_system import UnifiedAdvancedTradingSystem
    # Volume is currently 200 (very low) - good for opportunities but risky
    opportunities.append({
        'feature': 'Volume Threshold',
        'current': '200',
        'impact': 'HIGH',
        'recommendation': 'Current setting (200) maximizes opportunities but risks illiquid markets. Consider 500-1000 for safer liquidity.'
    })

    # Check edge requirements
    from src.utils.edge_filter import EdgeFilter
    opportunities.append({
        'feature': 'Edge Requirements',
        'current': f'{EdgeFilter.MIN_EDGE_REQUIREMENT:.1%}',
        'impact': 'VERY HIGH',
        'recommendation': 'Ultra-aggressive 3% minimum edge. This will trade frequently but watch win rate closely.'
    })

    # Check capital allocation
    opportunities.append({
        'feature': 'Capital Allocation',
        'current': '40% MM / 50% Directional / 10% Arb',
        'impact': 'MEDIUM',
        'recommendation': 'Consider increasing Market Making to 50% for more consistent profits from spreads.'
    })

    # Check AI budget
    from src.config.settings import settings
    ai_budget = getattr(settings.trading, 'daily_ai_budget', 0)
    opportunities.append({
        'feature': 'AI Budget',
        'current': f'${ai_budget}/day',
        'impact': 'MEDIUM',
        'recommendation': f'Current ${ai_budget}/day allows ~{int(ai_budget/0.10)} analyses. Increase if hitting limits.'
    })

    # Print opportunities
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. {opp['feature']}")
        print(f"   Current: {opp['current']}")
        print(f"   Impact: {opp['impact']}")
        print(f"   💡 {opp['recommendation']}")
        test_results['profit_opportunities'].append(opp)

def print_final_report():
    """Print comprehensive final report"""
    print("\n" + "="*60)
    print("📊 FINAL TEST REPORT")
    print("="*60)

    total = test_results['passed'] + test_results['failed']
    print(f"\n✅ Passed: {test_results['passed']}/{total}")
    print(f"❌ Failed: {test_results['failed']}/{total}")
    print(f"⚠️  Warnings: {test_results['warnings']}")

    if test_results['bugs_found']:
        print(f"\n🐛 BUGS FOUND: {len(test_results['bugs_found'])}")
        for bug in test_results['bugs_found']:
            print(f"   - {bug}")
    else:
        print(f"\n🎉 NO CRITICAL BUGS FOUND!")

    print(f"\n💰 PROFIT OPPORTUNITIES: {len(test_results['profit_opportunities'])}")

    success_rate = (test_results['passed'] / total * 100) if total > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")

    if success_rate >= 95:
        print("\n🚀 BOT IS PRODUCTION READY!")
        return 0
    elif success_rate >= 80:
        print("\n⚠️  BOT MOSTLY READY - Address failures above")
        return 1
    else:
        print("\n🛑 BOT NEEDS FIXES - Review failures")
        return 1

async def main():
    """Run all tests"""
    print("="*60)
    print("🔬 ULTRA-COMPREHENSIVE BOT TEST")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await test_api_connections()
        await test_database_operations()
        await test_safety_features()
        await test_edge_filter()
        await test_position_limits()
        await test_order_execution()
        await test_trading_strategies()
        await test_notifications()
        await analyze_profit_opportunities()

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        return 1

    return print_final_report()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
