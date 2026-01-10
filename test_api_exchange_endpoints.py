#!/usr/bin/env python3
"""
Test script to verify Kalshi API exchange endpoints (API Section Part 1).

Tests all endpoints from the Exchange section:
1. GET /exchange/status
2. GET /exchange/announcements
3. GET /series/fee_changes
4. GET /exchange/schedule
5. GET /exchange/user_data_timestamp
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.clients.kalshi_client import KalshiClient


async def test_exchange_status():
    """Test GET /exchange/status endpoint."""
    print("\n" + "=" * 60)
    print("TEST 1: GET /exchange/status")
    print("=" * 60)

    client = KalshiClient()

    try:
        status = await client.get_exchange_status()

        # Verify required fields per API docs
        assert 'exchange_active' in status, "Missing exchange_active field"
        assert 'trading_active' in status, "Missing trading_active field"
        assert isinstance(status['exchange_active'], bool), "exchange_active must be bool"
        assert isinstance(status['trading_active'], bool), "trading_active must be bool"

        print(f"✅ GET /exchange/status: Success")
        print(f"   Exchange active: {status['exchange_active']}")
        print(f"   Trading active: {status['trading_active']}")

        if 'exchange_estimated_resume_time' in status and status['exchange_estimated_resume_time']:
            print(f"   Estimated resume: {status['exchange_estimated_resume_time']}")

        return True

    except Exception as e:
        print(f"❌ GET /exchange/status FAILED: {e}")
        return False


async def test_exchange_announcements():
    """Test GET /exchange/announcements endpoint."""
    print("\n" + "=" * 60)
    print("TEST 2: GET /exchange/announcements")
    print("=" * 60)

    client = KalshiClient()

    try:
        result = await client.get_exchange_announcements()

        # Verify required fields per API docs
        assert 'announcements' in result, "Missing announcements field"
        assert isinstance(result['announcements'], list), "announcements must be array"

        print(f"✅ GET /exchange/announcements: Success")
        print(f"   Announcements count: {len(result['announcements'])}")

        # Show first few announcements if any
        for i, announcement in enumerate(result['announcements'][:3]):
            print(f"\n   Announcement {i+1}:")
            print(f"     Type: {announcement.get('type', 'N/A')}")
            print(f"     Status: {announcement.get('status', 'N/A')}")
            if 'message' in announcement:
                msg = announcement['message'][:100]  # Truncate long messages
                print(f"     Message: {msg}...")

        return True

    except Exception as e:
        print(f"❌ GET /exchange/announcements FAILED: {e}")
        return False


async def test_series_fee_changes():
    """Test GET /series/fee_changes endpoint."""
    print("\n" + "=" * 60)
    print("TEST 3: GET /series/fee_changes")
    print("=" * 60)

    client = KalshiClient()

    try:
        # Test without filters
        result = await client.get_series_fee_changes()

        assert 'series_fee_change_arr' in result, "Missing series_fee_change_arr field"
        assert isinstance(result['series_fee_change_arr'], list), "series_fee_change_arr must be array"

        print(f"✅ GET /series/fee_changes: Success")
        print(f"   Fee changes count: {len(result['series_fee_change_arr'])}")

        # Show first few if any
        for i, change in enumerate(result['series_fee_change_arr'][:2]):
            print(f"\n   Fee Change {i+1}:")
            print(f"     Series: {change.get('series_ticker', 'N/A')}")
            print(f"     Fee type: {change.get('fee_type', 'N/A')}")
            print(f"     Multiplier: {change.get('fee_multiplier', 'N/A')}")
            print(f"     Scheduled: {change.get('scheduled_ts', 'N/A')}")

        # Test with show_historical parameter
        result_hist = await client.get_series_fee_changes(show_historical=True)
        print(f"\n   With historical: {len(result_hist['series_fee_change_arr'])} total changes")

        return True

    except Exception as e:
        print(f"❌ GET /series/fee_changes FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_exchange_schedule():
    """Test GET /exchange/schedule endpoint."""
    print("\n" + "=" * 60)
    print("TEST 4: GET /exchange/schedule")
    print("=" * 60)

    client = KalshiClient()

    try:
        result = await client.get_exchange_schedule()

        # Verify required fields per API docs
        assert 'schedule' in result, "Missing schedule field"
        schedule = result['schedule']
        assert 'standard_hours' in schedule, "Missing standard_hours field"
        assert 'maintenance_windows' in schedule, "Missing maintenance_windows field"

        print(f"✅ GET /exchange/schedule: Success")
        print(f"   Standard hours entries: {len(schedule['standard_hours'])}")
        print(f"   Maintenance windows: {len(schedule['maintenance_windows'])}")

        # Show maintenance windows if any
        if schedule['maintenance_windows']:
            print("\n   Upcoming maintenance:")
            for i, window in enumerate(schedule['maintenance_windows'][:3]):
                print(f"     Window {i+1}: {window.get('start_datetime')} to {window.get('end_datetime')}")

        return True

    except Exception as e:
        print(f"❌ GET /exchange/schedule FAILED: {e}")
        return False


async def test_user_data_timestamp():
    """Test GET /exchange/user_data_timestamp endpoint."""
    print("\n" + "=" * 60)
    print("TEST 5: GET /exchange/user_data_timestamp")
    print("=" * 60)

    client = KalshiClient()

    try:
        result = await client.get_user_data_timestamp()

        # Verify required fields per API docs
        assert 'as_of_time' in result, "Missing as_of_time field"

        print(f"✅ GET /exchange/user_data_timestamp: Success")
        print(f"   Data as of: {result['as_of_time']}")

        # Parse and show data freshness
        try:
            as_of = datetime.fromisoformat(result['as_of_time'].replace('Z', '+00:00'))
            now = datetime.now(as_of.tzinfo)
            age_seconds = (now - as_of).total_seconds()
            print(f"   Data age: {age_seconds:.1f} seconds")

            if age_seconds < 1:
                print(f"   Status: ⚡ Very fresh!")
            elif age_seconds < 5:
                print(f"   Status: ✅ Fresh")
            elif age_seconds < 30:
                print(f"   Status: 🟡 Slightly delayed")
            else:
                print(f"   Status: 🔴 Delayed")

        except:
            pass

        print("\n   Per Kalshi API: Combine API responses with WebSocket data")
        print("   for most accurate exchange state view")

        return True

    except Exception as e:
        print(f"❌ GET /exchange/user_data_timestamp FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all exchange endpoint tests."""
    print("\n" + "=" * 70)
    print("KALSHI API - EXCHANGE ENDPOINTS VERIFICATION (API Part 1)")
    print("=" * 70)
    print("\nTesting all endpoints from API documentation Exchange section:")
    print("- GET /exchange/status")
    print("- GET /exchange/announcements")
    print("- GET /series/fee_changes")
    print("- GET /exchange/schedule")
    print("- GET /exchange/user_data_timestamp")

    results = []

    # Run all tests
    results.append(("GET /exchange/status", await test_exchange_status()))
    results.append(("GET /exchange/announcements", await test_exchange_announcements()))
    results.append(("GET /series/fee_changes", await test_series_fee_changes()))
    results.append(("GET /exchange/schedule", await test_exchange_schedule()))
    results.append(("GET /exchange/user_data_timestamp", await test_user_data_timestamp()))

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
        print("\n🎉 All Exchange endpoints verified successfully!")
        print("   Bot now implements:")
        print("   - Exchange status monitoring (trading hours, maintenance)")
        print("   - Exchange announcements (system notifications)")
        print("   - Series fee change tracking (anticipate fee updates)")
        print("   - Trading schedule (standard hours + maintenance windows)")
        print("   - Data freshness indicator (for accurate state tracking)")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
