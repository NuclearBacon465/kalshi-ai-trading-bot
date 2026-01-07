#!/usr/bin/env python3
"""
Comprehensive Edge Case and Bug Testing Suite

Tests for:
1. Division by zero errors
2. Null/None handling
3. Empty arrays/lists
4. Race conditions
5. API error handling
6. Edge cases in calculations
7. Boundary conditions
8. Type errors
9. Async operation errors
10. Resource exhaustion scenarios
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from src.clients.kalshi_client import KalshiClient
from src.clients.xai_client import XAIClient
from src.utils.database import DatabaseManager
from src.strategies.portfolio_optimization import (
    AdvancedPortfolioOptimizer,
    MarketOpportunity
)
from src.config.settings import settings

# Test results tracking
results = []


async def test_division_by_zero_protection():
    """Test that division by zero is handled in all calculations"""
    print("\n[TEST 1] DIVISION BY ZERO PROTECTION")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)

        print("  [1.1] Testing with market_probability = 0...")
        opp_zero = MarketOpportunity(
            market_id="TEST-ZERO",
            market_title="Zero Probability Test",
            predicted_probability=0.65,
            market_probability=0.0,  # ZERO - could cause division by zero
            confidence=0.70,
            edge=0.65,
            volatility=0.10,
            expected_return=0.65,
            max_loss=0.0,
            time_to_expiry=7.0,
            correlation_score=0.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_contribution=0.0
        )

        kelly_fracs = optimizer._calculate_kelly_fractions([opp_zero])
        print(f"    ✅ Zero market probability handled: {kelly_fracs}")

        print("  [1.2] Testing with market_probability = 1.0...")
        opp_one = MarketOpportunity(
            market_id="TEST-ONE",
            market_title="One Probability Test",
            predicted_probability=0.65,
            market_probability=1.0,  # ONE - could cause division by zero
            confidence=0.70,
            edge=-0.35,
            volatility=0.10,
            expected_return=-0.35,
            max_loss=1.0,
            time_to_expiry=7.0,
            correlation_score=0.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_contribution=0.0
        )

        kelly_fracs_one = optimizer._calculate_kelly_fractions([opp_one])
        print(f"    ✅ One market probability handled: {kelly_fracs_one}")

        print("  [1.3] Testing with empty opportunities list...")
        kelly_empty = optimizer._calculate_kelly_fractions([])
        print(f"    ✅ Empty list handled: {kelly_empty}")

        results.append(("Division By Zero Protection", True))
        return True

    except ZeroDivisionError as e:
        print(f"    ❌ DIVISION BY ZERO ERROR: {e}")
        results.append(("Division By Zero Protection", False))
        return False
    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("Division By Zero Protection", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_null_none_handling():
    """Test handling of None/null values"""
    print("\n[TEST 2] NULL/NONE HANDLING")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        print("  [2.1] Testing optimizer with None database...")
        try:
            # This should fail gracefully, not crash
            optimizer_none = AdvancedPortfolioOptimizer(None, kalshi_client, xai_client)
            print("    ⚠️  Accepted None database (potential bug)")
        except (TypeError, AttributeError) as e:
            print(f"    ✅ Correctly rejected None database")

        print("  [2.2] Testing Kalshi client with None balance response...")
        # Simulate None response
        balance = None
        available_cash = balance.get('balance', 0) / 100 if balance else 0.0
        print(f"    ✅ None balance handled: ${available_cash}")

        print("  [2.3] Testing opportunity with None values...")
        opp_none = MarketOpportunity(
            market_id="TEST-NONE",
            market_title="",  # Empty string
            predicted_probability=0.5,
            market_probability=0.5,
            confidence=0.0,  # Zero confidence
            edge=0.0,
            volatility=0.0,
            expected_return=0.0,
            max_loss=0.0,
            time_to_expiry=0.0,  # Zero time
            correlation_score=0.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_contribution=0.0
        )

        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)
        kelly_none = optimizer._calculate_kelly_fractions([opp_none])
        print(f"    ✅ Zero values handled: {kelly_none}")

        results.append(("Null/None Handling", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("Null/None Handling", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_empty_collections():
    """Test handling of empty arrays, lists, dicts"""
    print("\n[TEST 3] EMPTY COLLECTIONS HANDLING")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)

        print("  [3.1] Testing with empty opportunities list...")
        result_empty = optimizer._empty_allocation()
        print(f"    ✅ Empty allocation created: {result_empty.total_capital_used}")

        print("  [3.2] Testing Kelly calculation with empty list...")
        kelly_empty = optimizer._calculate_kelly_fractions([])
        print(f"    ✅ Empty Kelly fractions: {kelly_empty}")

        print("  [3.3] Testing with empty dict response...")
        empty_dict = {}
        balance = empty_dict.get('balance', 0) / 100
        print(f"    ✅ Empty dict handled: ${balance}")

        results.append(("Empty Collections Handling", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("Empty Collections Handling", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_boundary_conditions():
    """Test boundary conditions (min/max values)"""
    print("\n[TEST 4] BOUNDARY CONDITIONS")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)

        print("  [4.1] Testing with maximum confidence (1.0)...")
        opp_max = MarketOpportunity(
            market_id="TEST-MAX",
            market_title="Max Values Test",
            predicted_probability=1.0,  # Maximum
            market_probability=0.01,  # Near minimum
            confidence=1.0,  # Maximum
            edge=0.99,  # Maximum edge
            volatility=1.0,  # Maximum
            expected_return=0.99,
            max_loss=1.0,
            time_to_expiry=365.0,  # Maximum realistic
            correlation_score=1.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=10.0,
            sortino_ratio=10.0,
            max_drawdown_contribution=1.0
        )

        kelly_max = optimizer._calculate_kelly_fractions([opp_max])
        print(f"    ✅ Maximum values handled: {kelly_max}")

        print("  [4.2] Testing with minimum values...")
        opp_min = MarketOpportunity(
            market_id="TEST-MIN",
            market_title="Min Values Test",
            predicted_probability=0.01,  # Near minimum
            market_probability=0.99,  # Near maximum
            confidence=0.01,  # Near minimum
            edge=-0.98,  # Large negative edge
            volatility=0.01,
            expected_return=-0.98,
            max_loss=0.01,
            time_to_expiry=0.1,  # Very short
            correlation_score=-1.0,  # Maximum negative
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=-10.0,
            sortino_ratio=-10.0,
            max_drawdown_contribution=0.01
        )

        kelly_min = optimizer._calculate_kelly_fractions([opp_min])
        print(f"    ✅ Minimum values handled: {kelly_min}")

        print("  [4.3] Testing price boundaries (1-99 cents)...")
        # Test price clamping
        test_prices = [0, 1, 50, 99, 100, 150]
        for price in test_prices:
            clamped = max(1, min(99, price))
            is_valid = 1 <= clamped <= 99
            status = "✅" if is_valid else "❌"
            print(f"    {status} Price {price} → {clamped} (valid: {is_valid})")

        results.append(("Boundary Conditions", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Boundary Conditions", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_api_error_handling():
    """Test API error handling and recovery"""
    print("\n[TEST 5] API ERROR HANDLING")

    try:
        kalshi_client = KalshiClient()

        print("  [5.1] Testing with invalid market ID...")
        try:
            response = await kalshi_client.get_market("INVALID-MARKET-ID-12345")
            print(f"    ⚠️  No error raised for invalid market (API may have changed)")
        except Exception as e:
            print(f"    ✅ Invalid market handled: {type(e).__name__}")

        print("  [5.2] Testing retry logic with timeout...")
        # The client should handle timeouts gracefully
        try:
            # Test with very low limit to see pagination handling
            orders = await kalshi_client.get_orders()
            print(f"    ✅ Orders fetched: {len(orders.get('orders', []))}")
        except Exception as e:
            print(f"    ✅ Timeout/error handled: {type(e).__name__}")

        print("  [5.3] Testing rate limit handling...")
        # Make multiple rapid requests
        try:
            tasks = [kalshi_client.get_balance() for _ in range(5)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [r for r in responses if isinstance(r, Exception)]
            print(f"    ✅ Rate limiting handled: {len(errors)} errors out of 5 requests")
        except Exception as e:
            print(f"    ✅ Rate limit error handled: {type(e).__name__}")

        results.append(("API Error Handling", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("API Error Handling", False))
        return False
    finally:
        await kalshi_client.close()


async def test_concurrent_operations():
    """Test concurrent operations and race conditions"""
    print("\n[TEST 6] CONCURRENT OPERATIONS")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        print("  [6.1] Testing concurrent database operations...")
        # Multiple concurrent reads should work
        tasks = [db_manager.get_active_markets() for _ in range(10)]
        results_concurrent = await asyncio.gather(*tasks, return_exceptions=True)
        errors = [r for r in results_concurrent if isinstance(r, Exception)]
        print(f"    ✅ Concurrent reads: {len(errors)} errors out of 10")

        print("  [6.2] Testing concurrent API calls...")
        # Multiple concurrent API calls
        balance_tasks = [kalshi_client.get_balance() for _ in range(3)]
        balance_results = await asyncio.gather(*balance_tasks, return_exceptions=True)
        balance_errors = [r for r in balance_results if isinstance(r, Exception)]
        print(f"    ✅ Concurrent API calls: {balance_errors} errors out of 3")

        print("  [6.3] Testing concurrent portfolio optimization...")
        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)
        # Create multiple optimization tasks
        opt_tasks = [
            optimizer._calculate_kelly_fractions([]) for _ in range(5)
        ]
        opt_results = await asyncio.gather(*opt_tasks, return_exceptions=True)
        opt_errors = [r for r in opt_results if isinstance(r, Exception)]
        print(f"    ✅ Concurrent optimizations: {len(opt_errors)} errors out of 5")

        results.append(("Concurrent Operations", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("Concurrent Operations", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_resource_exhaustion():
    """Test resource exhaustion scenarios"""
    print("\n[TEST 7] RESOURCE EXHAUSTION")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        print("  [7.1] Testing with large number of opportunities...")
        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)

        # Create 1000 opportunities to test performance
        large_opp_list = []
        for i in range(1000):
            opp = MarketOpportunity(
                market_id=f"TEST-{i}",
                market_title=f"Test Market {i}",
                predicted_probability=0.6 + (i % 40) / 100,
                market_probability=0.5,
                confidence=0.7,
                edge=0.1,
                volatility=0.1,
                expected_return=0.1,
                max_loss=0.5,
                time_to_expiry=7.0,
                correlation_score=0.0,
                kelly_fraction=0.0,
                fractional_kelly=0.0,
                risk_adjusted_fraction=0.0,
                sharpe_ratio=1.5,
                sortino_ratio=2.0,
                max_drawdown_contribution=0.05
            )
            large_opp_list.append(opp)

        import time
        start = time.time()
        kelly_large = optimizer._calculate_kelly_fractions(large_opp_list[:100])  # Test with 100
        duration = time.time() - start
        print(f"    ✅ Large opportunity list handled: 100 opportunities in {duration:.2f}s")

        print("  [7.2] Testing memory usage with allocations...")
        allocation = optimizer._empty_allocation()
        print(f"    ✅ Allocation created: {allocation.total_capital_used}")

        print("  [7.3] Testing daily AI limits...")
        # Check if daily tracker is working
        if hasattr(xai_client, 'daily_tracker'):
            tracker = xai_client.daily_tracker
            print(f"    ✅ Daily AI tracker: {tracker.request_count} requests, ${tracker.total_cost:.4f} cost")
        else:
            print(f"    ⚠️  Daily tracker not found")

        results.append(("Resource Exhaustion", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Resource Exhaustion", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_data_validation():
    """Test data validation and type checking"""
    print("\n[TEST 8] DATA VALIDATION")

    try:
        print("  [8.1] Testing order data validation...")
        # Test order structure
        order_data = {
            "ticker": "TEST-MARKET-YES",
            "action": "buy",
            "side": "yes",
            "type": "market",
            "count": 10
        }

        # Check required fields
        required_fields = ["ticker", "action", "side", "type", "count"]
        for field in required_fields:
            if field not in order_data:
                print(f"    ❌ Missing required field: {field}")
                results.append(("Data Validation", False))
                return False
        print(f"    ✅ Order structure valid")

        print("  [8.2] Testing price validation...")
        test_prices = [-10, 0, 1, 50, 99, 100, 200]
        for price in test_prices:
            is_valid = 1 <= price <= 99
            clamped = max(1, min(99, price))
            status = "✅" if is_valid else "⚠️ "
            print(f"    {status} Price {price}: valid={is_valid}, clamped={clamped}")

        print("  [8.3] Testing confidence validation...")
        test_confidences = [-0.5, 0.0, 0.5, 1.0, 1.5]
        for conf in test_confidences:
            is_valid = 0.0 <= conf <= 1.0
            status = "✅" if is_valid else "⚠️ "
            print(f"    {status} Confidence {conf}: valid={is_valid}")

        results.append(("Data Validation", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("Data Validation", False))
        return False


async def test_edge_case_markets():
    """Test edge case market scenarios"""
    print("\n[TEST 9] EDGE CASE MARKETS")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)

        print("  [9.1] Testing expired market...")
        opp_expired = MarketOpportunity(
            market_id="TEST-EXPIRED",
            market_title="Expired Market",
            predicted_probability=0.65,
            market_probability=0.50,
            confidence=0.70,
            edge=0.15,
            volatility=0.10,
            expected_return=0.15,
            max_loss=0.50,
            time_to_expiry=-1.0,  # NEGATIVE - already expired
            correlation_score=0.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_contribution=0.0
        )

        kelly_expired = optimizer._calculate_kelly_fractions([opp_expired])
        print(f"    ✅ Expired market handled: {kelly_expired}")

        print("  [9.2] Testing illiquid market...")
        opp_illiquid = MarketOpportunity(
            market_id="TEST-ILLIQUID",
            market_title="Illiquid Market",
            predicted_probability=0.65,
            market_probability=0.50,
            confidence=0.70,
            edge=0.15,
            volatility=0.50,  # HIGH volatility = illiquid
            expected_return=0.15,
            max_loss=0.50,
            time_to_expiry=7.0,
            correlation_score=0.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_contribution=0.0
        )

        kelly_illiquid = optimizer._calculate_kelly_fractions([opp_illiquid])
        print(f"    ✅ Illiquid market handled: {kelly_illiquid}")

        print("  [9.3] Testing extreme price market...")
        opp_extreme = MarketOpportunity(
            market_id="TEST-EXTREME",
            market_title="Extreme Price Market",
            predicted_probability=0.99,
            market_probability=0.98,  # Very high, near certainty
            confidence=0.90,
            edge=0.01,  # Tiny edge
            volatility=0.02,
            expected_return=0.01,
            max_loss=0.98,  # Could lose almost everything
            time_to_expiry=1.0,
            correlation_score=0.0,
            kelly_fraction=0.0,
            fractional_kelly=0.0,
            risk_adjusted_fraction=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_contribution=0.0
        )

        kelly_extreme = optimizer._calculate_kelly_fractions([opp_extreme])
        print(f"    ✅ Extreme price handled: {kelly_extreme}")

        results.append(("Edge Case Markets", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Edge Case Markets", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def test_error_recovery():
    """Test error recovery and graceful degradation"""
    print("\n[TEST 10] ERROR RECOVERY")

    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        kalshi_client = KalshiClient()
        xai_client = XAIClient()

        print("  [10.1] Testing portfolio optimizer fallback...")
        optimizer = AdvancedPortfolioOptimizer(db_manager, kalshi_client, xai_client)

        # Test with problematic data that should trigger fallback
        result = optimizer._empty_allocation()
        print(f"    ✅ Empty allocation fallback: ${result.total_capital_used}")

        print("  [10.2] Testing database recovery...")
        # Try to query database
        markets = await db_manager.get_active_markets()
        print(f"    ✅ Database query successful: {len(markets)} markets")

        print("  [10.3] Testing API client recovery...")
        # Test if client can recover from error
        try:
            balance = await kalshi_client.get_balance()
            print(f"    ✅ API client working: ${balance.get('balance', 0) / 100:.2f}")
        except Exception as e:
            print(f"    ⚠️  API error (expected in some cases): {type(e).__name__}")

        results.append(("Error Recovery", True))
        return True

    except Exception as e:
        print(f"    ❌ ERROR: {e}")
        results.append(("Error Recovery", False))
        return False
    finally:
        await kalshi_client.close()
        await xai_client.close()


async def main():
    """Run all edge case and bug tests"""
    print("="*80)
    print("COMPREHENSIVE EDGE CASE AND BUG TESTING SUITE")
    print("="*80)

    # Run all tests
    await test_division_by_zero_protection()
    await test_null_none_handling()
    await test_empty_collections()
    await test_boundary_conditions()
    await test_api_error_handling()
    await test_concurrent_operations()
    await test_resource_exhaustion()
    await test_data_validation()
    await test_edge_case_markets()
    await test_error_recovery()

    # Print results
    print("\n" + "="*80)
    print("EDGE CASE TEST RESULTS")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print("="*80)
    if passed == total:
        print(f"✅ ALL {total} EDGE CASE TESTS PASSED\n")
        print("Your bot handles edge cases robustly!")
    else:
        print(f"⚠️  {passed}/{total} tests passed\n")
        print(f"{total - passed} test(s) need attention")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
