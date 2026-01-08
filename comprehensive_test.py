#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE SYSTEM TEST
Tests EVERYTHING: APIs, WebSocket, Grok, All Phases, Revolutionary Features
"""

import asyncio
import sys
import traceback
from datetime import datetime

test_results = {'passed': [], 'failed': [], 'warnings': []}

def print_header(text: str):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_test(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name:<45} | {details}")
    if passed:
        test_results['passed'].append(name)
    else:
        test_results['failed'].append((name, details))

def print_warning(name: str, details: str):
    print(f"⚠️  WARN | {name:<45} | {details}")
    test_results['warnings'].append((name, details))

async def test_database():
    print_header("TEST 1: DATABASE")
    try:
        from src.utils.database import DatabaseManager
        db = DatabaseManager()
        await db.initialize()
        print_test("Database initialization", True, "Created successfully")
        
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in await cursor.fetchall()]
            required = ['markets', 'positions', 'trade_logs', 'orders']
            all_exist = all(t in tables for t in required)
            print_test("Required tables exist", all_exist, f"{len(tables)} tables")
        
        return True
    except Exception as e:
        print_test("Database system", False, f"{e}")
        return False

async def test_kalshi_api():
    print_header("TEST 2: KALSHI API")
    try:
        from src.clients.kalshi_client import KalshiClient
        from src.config.settings import settings
        
        has_creds = bool(settings.kalshi_email and settings.kalshi_password)
        if not has_creds:
            print_warning("Kalshi credentials", "Not in .env (expected in test env)")
            return False
        
        print_test("Credentials configured", True, "Found")
        
        client = KalshiClient()
        print_test("Client initialization", True, "Created")
        
        try:
            balance_response = await client.get_balance()
            balance = balance_response.get('balance', 0) / 100
            print_test("Authentication & Balance", True, f"${balance:.2f}")
        except Exception as e:
            print_test("Authentication", False, f"{e}")
            await client.close()
            return False
        
        try:
            markets_response = await client.get_markets(limit=5)
            markets = markets_response.get('markets', [])
            print_test("Market data retrieval", len(markets) > 0, f"{len(markets)} markets")
        except Exception as e:
            print_test("Market data", False, f"{e}")
        
        await client.close()
        return True
    except Exception as e:
        print_test("Kalshi API", False, f"{e}")
        return False

async def test_xai_api():
    print_header("TEST 3: XAI / GROK API")
    try:
        from src.config.settings import settings
        import httpx
        
        has_key = bool(settings.xai_api_key)
        if not has_key:
            print_warning("xAI API key", "Not in .env - AI disabled")
            return False
        
        print_test("API key configured", True, f"{settings.xai_api_key[:10]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {settings.xai_api_key}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                models = response.json().get('data', [])
                model_names = [m.get('id') for m in models]
                print_test("API connection", True, f"{len(models)} models")
                
                has_grok = any('grok' in m.lower() for m in model_names)
                print_test("Grok models", has_grok, ", ".join(model_names[:3]))
            else:
                print_test("API connection", False, f"HTTP {response.status_code}")
        
        return True
    except Exception as e:
        print_test("xAI API", False, f"{e}")
        return False

async def test_websocket():
    print_header("TEST 4: WEBSOCKET REAL-TIME DATA")
    try:
        import websockets
        print_test("WebSockets library", True, f"v{websockets.__version__}")
    except ImportError:
        print_test("WebSockets library", False, "pip install websockets>=12.0")
        return False
    
    try:
        from src.clients.kalshi_client import KalshiClient
        from src.clients.kalshi_websocket import KalshiWebSocketClient
        
        kalshi = KalshiClient()
        ws = KalshiWebSocketClient(kalshi)
        print_test("WebSocket client", True, "Created")
        
        connected = await ws.connect()
        print_test("WS connection", connected, "Connected to Kalshi")
        
        if connected:
            received = [0]
            def on_update(data): received[0] += 1
            ws.on_ticker_update(on_update)
            
            from src.utils.database import DatabaseManager
            db = DatabaseManager()
            await db.initialize()
            markets = await db.get_eligible_markets(volume_min=1000, max_days_to_expiry=30)
            
            if markets:
                ticker = markets[0].market_id
                subscribed = await ws.subscribe_ticker(ticker)
                print_test("WS subscription", subscribed, ticker)
                
                if subscribed:
                    print("   Listening 5 seconds...")
                    listen_task = asyncio.create_task(ws.listen())
                    await asyncio.sleep(5)
                    listen_task.cancel()
                    try: await listen_task
                    except asyncio.CancelledError: pass
                    
                    updates = received[0]
                    print_test("Real-time streaming", updates > 0, f"{updates} updates in 5s")
                    if updates > 0:
                        print(f"   🚀 {updates/5:.1f} updates/sec!")
            
            await ws.close()
        
        await kalshi.close()
        return True
    except Exception as e:
        print_test("WebSocket", False, f"{e}")
        traceback.print_exc()
        return False

async def test_all_phases():
    print_header("TEST 5: ALL 4 TRADING PHASES")
    try:
        print("\n📦 PHASE 1: Core")
        from src.jobs.decide import make_decision_for_market
        from src.jobs.execute import execute_position
        print_test("Phase 1", True, "Core systems loaded")
        
        print("\n📊 PHASE 2: Advanced")
        from src.utils.advanced_position_sizing import AdvancedPositionSizer
        print_test("Phase 2", True, "Position sizing loaded")
        
        print("\n⚡ PHASE 3: Real-time")
        from src.utils.price_history import PriceHistoryTracker
        print_test("Phase 3", True, "Real-time data loaded")
        
        print("\n🏛️ PHASE 4: Institutional")
        from src.utils.smart_execution import SmartOrderExecutor
        from src.jobs.enhanced_execute import execute_position_enhanced
        from src.jobs.execute import ENHANCED_EXECUTION_AVAILABLE
        print_test("Phase 4", True, "Institutional features loaded")
        print_test("Phase 4 integration", ENHANCED_EXECUTION_AVAILABLE, "Enhanced execution active")
        
        return True
    except Exception as e:
        print_test("Trading Phases", False, f"{e}")
        return False

async def test_revolutionary_features():
    print_header("TEST 6: REVOLUTIONARY FEATURES")
    try:
        from src.utils.database import DatabaseManager
        db = DatabaseManager()
        await db.initialize()
        
        print("\n🧬 FEATURE 1: Strategy Evolution")
        from src.utils.adaptive_strategy_evolution import StrategyEvolution
        evolution = StrategyEvolution(db)
        population = await evolution.initialize_population()
        print_test("Strategy Evolution", len(population) == 20, f"{len(population)} strategies")
        
        print("\n💭 FEATURE 2: Sentiment Arbitrage")
        from src.utils.sentiment_arbitrage import SentimentArbitrageEngine
        sentiment = SentimentArbitrageEngine(db)
        analysis = await sentiment.analyze_sentiment("TEST", 0.65, 0.50, 5000)
        print_test("Sentiment Arbitrage", analysis is not None, f"Score: {analysis.sentiment_score:+.2f}")
        
        print("\n🎯 FEATURE 3: Bayesian Network")
        from src.utils.bayesian_belief_network import BayesianBeliefNetwork, Evidence, EvidenceType
        bayes = BayesianBeliefNetwork(db)
        belief = await bayes.initialize_belief("TEST", 0.50, 0.60)
        print_test("Bayesian Network", belief is not None, f"Prior: {belief.prior_probability:.1%}")
        
        print("\n📊 FEATURE 4: Regime Detection")
        from src.utils.market_regime_detection import MarketRegimeDetector
        detector = MarketRegimeDetector(db)
        print_test("Regime Detection", True, "Loaded successfully")
        
        return True
    except Exception as e:
        print_test("Revolutionary Features", False, f"{e}")
        traceback.print_exc()
        return False

async def test_bot_integration():
    print_header("TEST 7: BOT INTEGRATION")
    try:
        import beast_mode_bot
        print_test("Beast Mode Bot", True, "Main bot loads")
        
        from src.jobs.trade import run_trading_job
        print_test("Trading Job", True, "Unified system ready")
        
        import beast_mode_dashboard
        print_test("Dashboard", True, "Monitoring ready")
        
        return True
    except Exception as e:
        print_test("Bot Integration", False, f"{e}")
        return False

async def run_all_tests():
    print("""
╔════════════════════════════════════════════════════════════════╗
║     🧪 COMPREHENSIVE TEST - TESTING EVERYTHING! 🧪            ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    start = datetime.now()
    
    await test_database()
    await test_kalshi_api()
    await test_xai_api()
    await test_websocket()
    await test_all_phases()
    await test_revolutionary_features()
    await test_bot_integration()
    
    duration = (datetime.now() - start).total_seconds()
    
    print_header("FINAL RESULTS")
    
    total = len(test_results['passed']) + len(test_results['failed'])
    passed = len(test_results['passed'])
    failed = len(test_results['failed'])
    warnings = len(test_results['warnings'])
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"⏱️  Time: {duration:.1f}s")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%\n")
        
        if success_rate == 100:
            print("🎉 PERFECT! Everything works! 🎉")
        elif success_rate >= 90:
            print("🚀 EXCELLENT! Bot ready!")
        elif success_rate >= 75:
            print("✅ GOOD! Minor fixes needed")
        else:
            print("⚠️  WARNING! Issues need attention")
    
    if test_results['failed']:
        print("\n" + "="*70)
        print("FAILURES:")
        for name, details in test_results['failed']:
            print(f"❌ {name}: {details}")
    
    if test_results['warnings']:
        print("\n" + "="*70)
        print("WARNINGS:")
        for name, details in test_results['warnings']:
            print(f"⚠️  {name}: {details}")
    
    print("\n" + "="*70)
    return failed == 0

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
