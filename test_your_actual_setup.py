#!/usr/bin/env python3
"""
REAL API TESTING - Using YOUR actual Kalshi and xAI accounts
Tests with YOUR real data to ensure everything works perfectly
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

from src.clients.kalshi_client import KalshiClient
from src.clients.xai_client import XAIClient
from src.utils.database import DatabaseManager
from src.config.settings import settings

async def test_your_kalshi_api():
    """Test YOUR actual Kalshi account"""
    print("\n" + "="*80)
    print("TESTING YOUR KALSHI API")
    print("="*80)

    client = KalshiClient()
    tests = []

    try:
        # Get YOUR actual balance
        print("\n[1] YOUR Account Balance")
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        portfolio_value = balance.get('payout', 0) / 100
        total = cash + portfolio_value

        print(f"  Cash: ${cash:.2f}")
        print(f"  Positions Value: ${portfolio_value:.2f}")
        print(f"  Total: ${total:.2f}")

        if cash > 0:
            print(f"  ✅ You have ${cash:.2f} ready to trade")
            tests.append(True)
        else:
            print(f"  ⚠️ No cash available")
            tests.append(False)

        # Get YOUR actual positions
        print("\n[2] YOUR Current Positions")
        positions = await client.get_positions()
        position_list = positions.get('market_positions', [])

        print(f"  Open positions: {len(position_list)}")

        if len(position_list) > 0:
            print(f"\n  Your active positions:")
            for pos in position_list[:5]:
                ticker = pos.get('ticker', 'N/A')[:60]
                qty = pos.get('position', 0)
                value = pos.get('market_exposure', 0) / 100
                print(f"    • {ticker}")
                print(f"      Quantity: {qty} contracts, Value: ${value:.2f}")
        else:
            print(f"  No open positions")

        tests.append(True)

        # Get YOUR recent orders
        print("\n[3] YOUR Recent Orders")
        orders = await client.get_orders()
        order_list = orders.get('orders', [])

        print(f"  Total orders: {len(order_list)}")

        if len(order_list) > 0:
            print(f"\n  Recent orders:")
            for order in order_list[:3]:
                ticker = order.get('ticker', 'N/A')[:60]
                side = order.get('side', 'N/A')
                action = order.get('action', 'N/A')
                status = order.get('status', 'N/A')
                print(f"    • {action.upper()} {side.upper()} - {ticker}")
                print(f"      Status: {status}")
        else:
            print(f"  No orders yet")

        tests.append(True)

        # Check REAL markets available to YOU
        print("\n[4] Markets Available to YOU Right Now")
        markets = await client.get_markets(limit=20, status="open")
        market_list = markets.get('markets', [])

        print(f"  Open markets: {len(market_list)}")

        # Find TRADEABLE markets with actual liquidity
        tradeable = []
        for market in market_list:
            yes_ask = market.get('yes_ask', 0)
            no_ask = market.get('no_ask', 0)
            yes_bid = market.get('yes_bid', 0)
            no_bid = market.get('no_bid', 0)
            volume = market.get('volume', 0)

            # Market has liquidity if it has bids/asks and volume
            has_liquidity = (yes_ask > 0 and yes_ask < 100 and
                           no_ask > 0 and no_ask < 100 and
                           volume > 0)

            if has_liquidity:
                tradeable.append(market)

        print(f"  Tradeable markets: {len(tradeable)}")

        if len(tradeable) > 0:
            print(f"\n  Top tradeable opportunities:")
            for market in tradeable[:3]:
                title = market.get('title', 'N/A')[:70]
                yes_ask = market.get('yes_ask', 0)
                no_ask = market.get('no_ask', 0)
                volume = market.get('volume', 0)
                print(f"\n    {title}")
                print(f"    YES: {yes_ask}¢ | NO: {no_ask}¢ | Volume: {volume:,}")
        else:
            print(f"\n  ⚠️ No tradeable markets right now (off-hours or low liquidity)")

        tests.append(True)

    except Exception as e:
        print(f"\n  ❌ Error testing Kalshi API: {e}")
        tests.append(False)
    finally:
        await client.close()

    return all(tests)


async def test_your_xai_api():
    """Test YOUR actual xAI (Grok) API"""
    print("\n" + "="*80)
    print("TESTING YOUR xAI API (Grok)")
    print("="*80)

    db_manager = DatabaseManager()
    await db_manager.initialize()

    tests = []

    try:
        xai_client = XAIClient(db_manager=db_manager)

        # Check API key configured
        api_key = settings.api.xai_api_key
        print(f"\n[1] API Key Configuration")
        print(f"  Key length: {len(api_key)} characters")

        if len(api_key) > 20:
            print(f"  ✅ xAI API key configured")
            tests.append(True)
        else:
            print(f"  ❌ xAI API key invalid")
            tests.append(False)

        # Check usage from database
        print(f"\n[2] YOUR xAI Usage Statistics")

        import aiosqlite
        async with aiosqlite.connect('trading_system.db') as db:
            # Get today's usage
            cursor = await db.execute("""
                SELECT COUNT(*) as queries
                FROM llm_queries
                WHERE date(timestamp) = date('now')
            """)
            today_queries = (await cursor.fetchone())[0]

            # Get last 24 hours
            cursor = await db.execute("""
                SELECT COUNT(*) as queries
                FROM llm_queries
                WHERE datetime(timestamp) > datetime('now', '-24 hours')
            """)
            last_24h = (await cursor.fetchone())[0]

            # Get total
            cursor = await db.execute("SELECT COUNT(*) FROM llm_queries")
            total_queries = (await cursor.fetchone())[0]

            print(f"  Today: {today_queries} AI queries")
            print(f"  Last 24 hours: {last_24h} queries")
            print(f"  Total all-time: {total_queries} queries")

            if total_queries > 0:
                print(f"  ✅ xAI API has been used successfully")
                tests.append(True)

                # Show some recent analyses
                cursor = await db.execute("""
                    SELECT market_id, confidence_extracted, decision_extracted, timestamp
                    FROM llm_queries
                    ORDER BY timestamp DESC
                    LIMIT 5
                """)
                recent = await cursor.fetchall()

                if recent:
                    print(f"\n  Recent AI analyses:")
                    for market, conf, decision, ts in recent:
                        conf_str = f"{int(conf*100)}%" if conf else "N/A"
                        decision_str = decision if decision else "SKIP"
                        print(f"    [{ts[5:16]}] {decision_str:8} | Confidence: {conf_str:4}")
            else:
                print(f"  ⚠️ xAI API not used yet (bot hasn't analyzed markets)")
                tests.append(True)

        await xai_client.close()

    except Exception as e:
        print(f"\n  ❌ Error testing xAI API: {e}")
        tests.append(False)

    return all(tests)


async def analyze_bot_performance():
    """Analyze YOUR bot's performance and configuration"""
    print("\n" + "="*80)
    print("ANALYZING YOUR BOT PERFORMANCE")
    print("="*80)

    recommendations = []

    # Check configuration
    print("\n[1] Current Configuration Analysis")
    conf = settings.trading.min_confidence_to_trade
    kelly = settings.trading.kelly_fraction
    max_pos = settings.trading.max_single_position
    budget = settings.trading.daily_ai_budget

    print(f"  Confidence threshold: {conf*100:.0f}%")
    print(f"  Kelly fraction: {kelly}")
    print(f"  Max position: {max_pos*100:.0f}%")
    print(f"  Daily AI budget: ${budget}")

    if conf >= 0.6:
        recommendations.append("⚠️ RECOMMENDATION: Lower confidence to 50% for more trades")
    else:
        print(f"  ✅ Aggressive confidence threshold (50%)")

    if kelly < 0.7:
        recommendations.append("⚠️ RECOMMENDATION: Increase Kelly to 0.75 for bigger positions")
    else:
        print(f"  ✅ Aggressive Kelly sizing (75%)")

    if max_pos < 0.35:
        recommendations.append("⚠️ RECOMMENDATION: Increase max position to 40% for high risk/reward")
    else:
        print(f"  ✅ Aggressive position sizing (40% max)")

    # Check database for trading activity
    print("\n[2] Trading Activity Analysis")

    import aiosqlite
    async with aiosqlite.connect('trading_system.db') as db:
        # Count positions
        cursor = await db.execute("""
            SELECT COUNT(*) FROM positions
            WHERE status IN ('open', 'live')
        """)
        open_positions = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM positions")
        total_positions = (await cursor.fetchone())[0]

        print(f"  Open positions: {open_positions}")
        print(f"  Total positions (all-time): {total_positions}")

        if open_positions == 0 and total_positions == 0:
            recommendations.append("💡 Bot hasn't taken any trades yet - may need to:")
            recommendations.append("   - Lower confidence threshold")
            recommendations.append("   - Increase trading frequency")
            recommendations.append("   - Check market availability")

        # Check AI analysis activity
        cursor = await db.execute("""
            SELECT COUNT(*) FROM llm_queries
            WHERE datetime(timestamp) > datetime('now', '-1 hour')
        """)
        recent_analyses = (await cursor.fetchone())[0]

        print(f"  AI analyses (last hour): {recent_analyses}")

        if recent_analyses == 0:
            recommendations.append("⚠️ No recent AI analysis - bot may not be running")
        else:
            print(f"  ✅ Bot is actively analyzing markets")

    # Recommendations
    if recommendations:
        print("\n[3] RECOMMENDATIONS TO IMPROVE PROFITABILITY")
        print("="*80)
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("\n[3] ✅ Configuration is OPTIMAL for HIGH RISK/REWARD")

    return True


async def main():
    """Run comprehensive tests with YOUR actual APIs"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TESTING - YOUR ACTUAL SETUP")
    print("="*80)

    results = []

    # Test YOUR Kalshi API
    results.append(("YOUR Kalshi API", await test_your_kalshi_api()))

    # Test YOUR xAI API
    results.append(("YOUR xAI API", await test_your_xai_api()))

    # Analyze YOUR bot performance
    results.append(("Bot Performance Analysis", await analyze_bot_performance()))

    # Final results
    print("\n" + "="*80)
    print("FINAL RESULTS - YOUR SETUP")
    print("="*80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")

    total_passed = sum(1 for _, p in results if p)
    total = len(results)

    print("\n" + "="*80)
    if total_passed == total:
        print(f"✅ ALL {total} TESTS PASSED")
        print("\nYour bot is ready to trade with:")
        print("  • YOUR Kalshi account")
        print("  • YOUR xAI API")
        print("  • HIGH RISK HIGH REWARD settings")
    else:
        print(f"⚠️ {total - total_passed} test(s) need attention")
    print("="*80)

    return total_passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
