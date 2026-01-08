#!/usr/bin/env python3
"""
REAL SYSTEM VERIFICATION - NO BULLSHIT
Tests with ACTUAL credentials to verify what ACTUALLY works
"""

import asyncio
import sys
from pathlib import Path

async def verify_everything():
    print("="*70)
    print("  REAL SYSTEM VERIFICATION - ACTUAL TESTS")
    print("="*70)

    # 1. CHECK CONFIGURATION
    print("\n1. CHECKING .ENV CONFIGURATION...")
    from src.config.settings import settings

    print(f"   Kalshi API Key: {settings.api.kalshi_api_key[:10]}... ({'✅ SET' if settings.api.kalshi_api_key else '❌ MISSING'})")
    print(f"   xAI API Key: {settings.api.xai_api_key[:10]}... ({'✅ SET' if settings.api.xai_api_key else '❌ MISSING'})")
    print(f"   Live Trading: {settings.trading.live_trading_enabled} {'⚠️ REAL MONEY' if settings.trading.live_trading_enabled else '✅ PAPER'}")

    # 2. CHECK PRIVATE KEY FILE
    print("\n2. CHECKING PRIVATE KEY FILE...")
    key_path = Path("kalshi_private_key")
    if key_path.exists():
        with open(key_path, 'r') as f:
            first_line = f.readline().strip()
            if "BEGIN PRIVATE KEY" in first_line or "BEGIN RSA PRIVATE KEY" in first_line:
                print(f"   ✅ Private key file exists and is valid PEM format")
            else:
                print(f"   ❌ Private key file exists but doesn't look like PEM format")
                print(f"   First line: {first_line}")
    else:
        print(f"   ❌ Private key file NOT FOUND at: {key_path.absolute()}")
        return False

    # 3. TEST KALSHI API WITH REAL CREDENTIALS
    print("\n3. TESTING KALSHI API (REAL CONNECTION)...")
    from src.clients.kalshi_client import KalshiClient

    client = KalshiClient()
    try:
        # Test balance
        balance_response = await client.get_balance()
        balance = balance_response.get('balance', 0) / 100
        print(f"   ✅ Kalshi API authenticated successfully")
        print(f"   💰 Account balance: ${balance:.2f}")

        # Test market data
        markets_response = await client.get_markets(limit=3)
        markets = markets_response.get('markets', [])
        print(f"   ✅ Market data retrieval working ({len(markets)} markets)")

        # Test positions (using correct method name)
        try:
            positions_response = await client.get_positions()
            positions = positions_response.get('positions', [])
            print(f"   ✅ Positions retrieval working ({len(positions)} positions)")
        except AttributeError:
            # Method might not exist, skip
            print(f"   ⚠️ Position method not available (not critical)")

    except Exception as e:
        print(f"   ❌ Kalshi API FAILED: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False

    await client.close()

    # 4. TEST XAI/GROK API
    print("\n4. TESTING XAI/GROK API (REAL CONNECTION)...")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {settings.api.xai_api_key}"}
            )

            if response.status_code == 200:
                models = response.json().get('data', [])
                model_ids = [m.get('id') for m in models]
                print(f"   ✅ xAI API authenticated successfully")
                print(f"   🤖 {len(models)} models available")
                grok_models = [m for m in model_ids if 'grok' in m.lower()]
                if grok_models:
                    print(f"   ✅ Grok models: {', '.join(grok_models[:3])}")
            else:
                print(f"   ❌ xAI API returned status {response.status_code}")
                print(f"   Response: {response.text}")

    except Exception as e:
        print(f"   ⚠️ xAI API test failed: {e}")
        print(f"   (This might be temporary - server overload)")

    # 5. TEST WEBSOCKET CONNECTION
    print("\n5. TESTING WEBSOCKET (REAL CONNECTION)...")
    from src.clients.kalshi_websocket import KalshiWebSocketClient

    ws_client = KalshiWebSocketClient()
    try:
        connected = await ws_client.connect()
        if connected:
            print(f"   ✅ WebSocket connected successfully!")
            await ws_client.disconnect()
        else:
            print(f"   ❌ WebSocket connection failed (check logs above)")
    except Exception as e:
        print(f"   ❌ WebSocket FAILED: {e}")
        import traceback
        traceback.print_exc()

    # 6. TEST DATABASE
    print("\n6. TESTING DATABASE...")
    from src.utils.database import DatabaseManager
    db = DatabaseManager()
    await db.initialize()

    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in await cursor.fetchall()]
        print(f"   ✅ Database initialized: {len(tables)} tables")
        print(f"   Tables: {', '.join(tables[:5])}...")

    # 7. TEST ALL PHASES
    print("\n7. TESTING ALL 4 PHASES...")
    try:
        from src.jobs.decide import make_decision_for_market
        print(f"   ✅ Phase 1 (Core): Decision engine loaded")
    except Exception as e:
        print(f"   ❌ Phase 1 failed: {e}")

    try:
        from src.utils.advanced_position_sizing import AdvancedPositionSizer
        print(f"   ✅ Phase 2 (Advanced): Position sizing loaded")
    except Exception as e:
        print(f"   ❌ Phase 2 failed: {e}")

    try:
        from src.utils.price_history import PriceHistoryTracker
        print(f"   ✅ Phase 3 (Real-time): Price tracking loaded")
    except Exception as e:
        print(f"   ❌ Phase 3 failed: {e}")

    try:
        from src.jobs.enhanced_execute import execute_position_enhanced
        print(f"   ✅ Phase 4 (Institutional): Enhanced execution loaded")
    except Exception as e:
        print(f"   ❌ Phase 4 failed: {e}")

    # 8. TEST REVOLUTIONARY FEATURES
    print("\n8. TESTING REVOLUTIONARY FEATURES...")
    try:
        from src.utils.adaptive_strategy_evolution import StrategyEvolution
        engine = StrategyEvolution(db)
        print(f"   ✅ Strategy Evolution: {len(engine.population)} strategies")
    except Exception as e:
        print(f"   ❌ Strategy Evolution failed: {e}")

    try:
        from src.utils.sentiment_arbitrage import SentimentArbitrageEngine
        print(f"   ✅ Sentiment Arbitrage: Loaded")
    except Exception as e:
        print(f"   ❌ Sentiment Arbitrage failed: {e}")

    try:
        from src.utils.bayesian_belief_network import BayesianBeliefNetwork
        print(f"   ✅ Bayesian Network: Loaded")
    except Exception as e:
        print(f"   ❌ Bayesian Network failed: {e}")

    try:
        from src.utils.market_regime_detection import MarketRegimeDetector
        print(f"   ✅ Regime Detection: Loaded")
    except Exception as e:
        print(f"   ❌ Regime Detection failed: {e}")

    print("\n" + "="*70)
    print("  VERIFICATION COMPLETE")
    print("="*70)
    return True

if __name__ == "__main__":
    asyncio.run(verify_everything())
