#!/usr/bin/env python3
"""
Beast Mode Trading Bot 🚀

Main entry point for the Unified Advanced Trading System that orchestrates:
- Market Making Strategy (40% allocation)
- Directional Trading with Portfolio Optimization (50% allocation) 
- Arbitrage Detection (10% allocation)

Features:
- No time restrictions (trade any deadline)
- Dynamic exit strategies
- Kelly Criterion portfolio optimization
- Real-time risk management
- Market making for spread profits

Usage:
    python beast_mode_bot.py              # Paper trading mode
    python beast_mode_bot.py --live       # Live trading mode
    python beast_mode_bot.py --dashboard  # Live dashboard mode
"""

import asyncio
import argparse
import time
import signal
from datetime import datetime, timedelta
from typing import Optional, Tuple
import aiosqlite

from src.jobs.trade import run_trading_job
from src.jobs.ingest import run_ingestion
from src.jobs.track import run_tracking
from src.jobs.evaluate import run_evaluation
from src.utils.logging_setup import setup_logging, get_trading_logger
from src.utils.database import DatabaseManager, Order
from src.utils.risk_cooldown import is_risk_cooldown_active
from src.clients.kalshi_client import KalshiClient
from src.clients.xai_client import XAIClient
from src.config.settings import settings
from src.utils.health import is_safe_mode_active

# Import Beast Mode components
from src.strategies.unified_trading_system import run_unified_trading_system, TradingSystemConfig
from beast_mode_dashboard import BeastModeDashboard


class BeastModeBot:
    """
    Beast Mode Trading Bot - Advanced Multi-Strategy Trading System 🚀
    
    This bot orchestrates all advanced strategies:
    1. Market Making (spread profits)
    2. Directional Trading (AI predictions with portfolio optimization)
    3. Arbitrage Detection (future feature)
    
    Features:
    - Unlimited market deadlines with dynamic exits
    - Cost controls and budget management
    - Real-time performance monitoring
    - Risk management and rebalancing
    """
    
    def __init__(
        self,
        live_mode: bool = False,
        dashboard_mode: bool = False,
        scan_interval_seconds: int = 60
    ):
        self.live_mode = live_mode
        self.dashboard_mode = dashboard_mode
        self.scan_interval_seconds = scan_interval_seconds
        self.logger = get_trading_logger("beast_mode_bot")
        self.shutdown_event = asyncio.Event()
        
        # Set live trading in settings
        settings.trading.live_trading_enabled = live_mode
        settings.trading.paper_trading_mode = not live_mode
        
        self.logger.info(
            f"🚀 Beast Mode Bot initialized - "
            f"Mode: {'LIVE TRADING' if live_mode else 'PAPER TRADING'}"
        )

    async def run_dashboard_mode(self):
        """Run in live dashboard mode with real-time updates."""
        try:
            self.logger.info("🚀 Starting Beast Mode Dashboard Mode")
            dashboard = BeastModeDashboard()
            await dashboard.show_live_dashboard()
        except KeyboardInterrupt:
            self.logger.info("👋 Dashboard mode stopped")
        except Exception as e:
            self.logger.error(f"Error in dashboard mode: {e}")

    async def run_trading_mode(self):
        """Run the Beast Mode trading system with all strategies."""
        try:
            self.logger.info("🚀 BEAST MODE TRADING BOT STARTED")
            self.logger.info(f"📊 Trading Mode: {'LIVE' if self.live_mode else 'PAPER'}")
            self.logger.info(f"💰 Daily AI Budget: ${settings.trading.daily_ai_budget}")
            self.logger.info(f"⚡ Features: Market Making + Portfolio Optimization + Dynamic Exits")
            self.logger.info(f"⏱️ Trading cycle interval: {self.scan_interval_seconds}s")
            
            # 🚨 CRITICAL FIX: Initialize database FIRST and wait for completion
            self.logger.info("🔧 Initializing database...")
            db_manager = DatabaseManager()
            await self._ensure_database_ready(db_manager)
            self.logger.info("✅ Database initialization complete!")
            
            # Initialize other components
            kalshi_client = KalshiClient()
            xai_client = XAIClient(db_manager=db_manager)  # Pass db_manager for LLM logging

            # 🚀 PHASE 3: Initialize advanced features
            self.logger.info("🚀 Initializing Phase 3 features...")

            # Initialize price history tracking
            try:
                from src.utils.price_history import get_price_tracker
                price_tracker = await get_price_tracker(db_manager)
                self.logger.info("✅ Price history tracking initialized")
            except Exception as e:
                self.logger.warning(f"Price history not available: {e}")
                price_tracker = None

            # Initialize WebSocket manager (real-time data)
            try:
                from src.utils.websocket_manager import get_websocket_manager
                ws_manager = await get_websocket_manager(db_manager)
                self.logger.info("✅ WebSocket manager initialized (300x faster updates!)")
            except Exception as e:
                self.logger.warning(f"WebSocket manager not available: {e}")
                ws_manager = None

            # 🚀 PHASE 4: Initialize institutional-grade features
            self.logger.info("🚀 Initializing Phase 4 institutional-grade features...")

            # Initialize smart execution engine
            try:
                from src.utils.smart_execution import SmartOrderExecutor
                smart_executor = SmartOrderExecutor(kalshi_client, db_manager)
                self.logger.info("✅ Smart execution engine initialized (order book analysis + adversarial detection)")
            except Exception as e:
                self.logger.warning(f"Smart executor not available: {e}")
                smart_executor = None

            # Initialize inventory manager
            try:
                from src.utils.inventory_management import get_inventory_manager
                inventory_manager = await get_inventory_manager(db_manager)
                self.logger.info("✅ Inventory risk management initialized")
            except Exception as e:
                self.logger.warning(f"Inventory manager not available: {e}")
                inventory_manager = None

            self.logger.info("🎯 Phase 4 features ready - institutional-grade execution enabled!")

            # Sync startup state (orders + positions) and cancel stale orders
            await self._sync_startup_state(db_manager, kalshi_client)
            
            # Small delay to ensure everything is ready
            await asyncio.sleep(1)
            
            # Start market ingestion first
            self.logger.info("🔄 Starting market ingestion...")
            market_ingestion_factory = lambda: asyncio.create_task(
                self._run_market_ingestion(db_manager, kalshi_client),
                name="market_ingestion",
            )
            ingestion_task = market_ingestion_factory()
            
            # Wait for initial market data ingestion
            await asyncio.sleep(10)
            
            # Run remaining background tasks
            self.logger.info("🚀 Starting trading and monitoring tasks...")
            task_factories = {
                "market_ingestion": market_ingestion_factory,
                "trading_cycles": lambda: asyncio.create_task(
                    self._run_trading_cycles(db_manager, kalshi_client, xai_client, price_tracker, ws_manager),
                    name="trading_cycles",
                ),
                "position_tracking": lambda: asyncio.create_task(
                    self._run_position_tracking(db_manager, kalshi_client),
                    name="position_tracking",
                ),
                "performance_evaluation": lambda: asyncio.create_task(
                    self._run_performance_evaluation(db_manager),
                    name="performance_evaluation",
                ),
            }
            restart_counts = {name: 0 for name in task_factories}
            tasks = {"market_ingestion": ingestion_task}
            for name, factory in task_factories.items():
                if name == "market_ingestion":
                    continue
                tasks[name] = factory()
            
            # Setup shutdown handler
            def signal_handler():
                self.logger.info("🛑 Shutdown signal received")
                self.shutdown_event.set()
                for task in tasks.values():
                    task.cancel()
            
            # Handle Ctrl+C gracefully
            for sig in [signal.SIGINT, signal.SIGTERM]:
                signal.signal(sig, lambda s, f: signal_handler())
            
            # Supervisor loop for task failures
            while not self.shutdown_event.is_set():
                if not tasks:
                    self.logger.error("No active tasks remaining; initiating shutdown")
                    self.shutdown_event.set()
                    break
                done, _ = await asyncio.wait(
                    tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for name, task in list(tasks.items()):
                    if task not in done:
                        continue

                    if task.cancelled():
                        self.logger.warning("Task %s was cancelled", name)
                        del tasks[name]
                        continue

                    exception = task.exception()
                    if exception:
                        self.logger.error(
                            "Task %s failed with an exception",
                            name,
                            exc_info=exception,
                        )
                    else:
                        self.logger.warning("Task %s exited unexpectedly", name)

                    del tasks[name]
                    restart_counts[name] += 1
                    if not settings.trading.restart_failed_tasks:
                        self.logger.error(
                            "Restart policy disabled; initiating shutdown after %s exit",
                            name,
                        )
                        self.shutdown_event.set()
                        break

                    if restart_counts[name] > settings.trading.max_task_restarts:
                        self.logger.error(
                            "Task %s exceeded max restarts (%d); initiating shutdown",
                            name,
                            settings.trading.max_task_restarts,
                        )
                        self.shutdown_event.set()
                        break

                    delay = settings.trading.task_restart_delay_seconds
                    if delay > 0:
                        self.logger.info(
                            "Restarting %s after %d seconds (attempt %d/%d)",
                            name,
                            delay,
                            restart_counts[name],
                            settings.trading.max_task_restarts,
                        )
                        await asyncio.sleep(delay)
                    tasks[name] = task_factories[name]()

            for task in tasks.values():
                task.cancel()
            await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            await xai_client.close()
            await kalshi_client.close()
            
            self.logger.info("🏁 Beast Mode Bot shut down gracefully")
            
        except Exception as e:
            self.logger.error(f"Error in Beast Mode Bot: {e}")
            raise

    async def _ensure_database_ready(self, db_manager: DatabaseManager):
        """Ensure database is fully initialized before starting any tasks."""
        try:
            # Initialize the database first to create all tables
            await db_manager.initialize()
            
            # Verify tables exist by checking one of them
            import aiosqlite
            async with aiosqlite.connect(db_manager.db_path) as db:
                await db.execute("SELECT COUNT(*) FROM positions LIMIT 1")
                await db.execute("SELECT COUNT(*) FROM markets LIMIT 1") 
                await db.execute("SELECT COUNT(*) FROM trade_logs LIMIT 1")
                await db.execute("SELECT COUNT(*) FROM orders LIMIT 1")
            
            self.logger.info("🎯 Database tables verified and ready")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    async def _sync_startup_state(self, db_manager: DatabaseManager, kalshi_client: KalshiClient):
        """Sync orders and positions from Kalshi on startup."""
        self.logger.info("🔄 Syncing startup orders and positions from Kalshi...")

        orders_response = await kalshi_client.get_orders(status="open")
        orders_raw = orders_response.get("orders", orders_response.get("order", [])) or []

        positions_response = await kalshi_client.get_positions()
        positions_raw = positions_response.get("positions", []) or []

        self.logger.info(
            f"📌 Startup sync: {len(orders_raw)} open orders, {len(positions_raw)} positions"
        )

        orders = []
        for order_data in orders_raw:
            normalized = self._normalize_order(order_data)
            if normalized:
                orders.append(normalized)

        await db_manager.upsert_orders(orders)
        await self._cancel_stale_orders(kalshi_client, db_manager, orders_raw)

    def _normalize_order(self, order_data: dict) -> Optional[Order]:
        """Normalize a Kalshi order payload into an Order dataclass."""
        order_id = order_data.get("order_id") or order_data.get("id")
        ticker = order_data.get("ticker") or order_data.get("market_ticker")
        status = order_data.get("status")
        if not order_id or not ticker or not status:
            self.logger.warning("Skipping order with missing identifiers", order_data=order_data)
            return None

        created_ts = self._parse_timestamp(
            order_data.get("created_ts")
            or order_data.get("created_time")
            or order_data.get("created_at")
        )
        updated_ts = self._parse_timestamp(
            order_data.get("updated_ts")
            or order_data.get("updated_time")
            or order_data.get("updated_at")
        )

        return Order(
            order_id=order_id,
            ticker=ticker,
            status=status,
            side=order_data.get("side"),
            action=order_data.get("action"),
            type=order_data.get("type"),
            yes_price=order_data.get("yes_price"),
            no_price=order_data.get("no_price"),
            count=order_data.get("count"),
            remaining_count=order_data.get("remaining_count") or order_data.get("remaining_qty"),
            created_ts=created_ts,
            updated_ts=updated_ts,
            client_order_id=order_data.get("client_order_id"),
            expiration_ts=order_data.get("expiration_ts") or order_data.get("expire_ts"),
            last_synced=datetime.utcnow()
        )

    def _parse_timestamp(self, value: Optional[object]) -> Optional[int]:
        """Parse timestamp values from API responses into seconds since epoch."""
        if value is None:
            return None
        try:
            timestamp = int(value)
        except (TypeError, ValueError):
            return None
        if timestamp > 1_000_000_000_000:
            return timestamp // 1000
        return timestamp

    async def _cancel_stale_orders(
        self,
        kalshi_client: KalshiClient,
        db_manager: DatabaseManager,
        orders_raw: list[dict]
    ):
        """Cancel stale open orders based on age or price drift."""
        if not orders_raw:
            return

        max_age_minutes = getattr(settings.trading, 'stale_order_max_age_minutes', 60)
        max_price_drift = getattr(settings.trading, 'stale_order_price_drift_cents', 5)
        now_ts = int(time.time())
        market_cache: dict[str, dict] = {}

        for order in orders_raw:
            order_id = order.get("order_id") or order.get("id")
            ticker = order.get("ticker") or order.get("market_ticker")
            if not order_id or not ticker:
                continue

            created_ts = self._parse_timestamp(
                order.get("created_ts")
                or order.get("created_time")
                or order.get("created_at")
            )

            is_stale = False
            if created_ts:
                age_minutes = (now_ts - created_ts) / 60
                if age_minutes >= max_age_minutes:
                    is_stale = True
                    self.logger.info(
                        "🕒 Cancelling stale order by age",
                        order_id=order_id,
                        ticker=ticker,
                        age_minutes=f"{age_minutes:.1f}"
                    )

            if not is_stale:
                order_type = order.get("type")
                if order_type == "limit":
                    market = market_cache.get(ticker)
                    if market is None:
                        market = await kalshi_client.get_market(ticker)
                        market_cache[ticker] = market

                    order_price = (
                        order.get("yes_price")
                        if order.get("yes_price") is not None
                        else order.get("no_price")
                    )
                    price_reference = self._get_price_reference(order, market)

                    if order_price is not None and price_reference is not None:
                        price_drift = abs(order_price - price_reference)
                        if price_drift >= max_price_drift:
                            is_stale = True
                            self.logger.info(
                                "📉 Cancelling stale order by price drift",
                                order_id=order_id,
                                ticker=ticker,
                                order_price=order_price,
                                price_reference=price_reference,
                                price_drift=price_drift
                            )

            if is_stale:
                try:
                    await kalshi_client.cancel_order(order_id)
                    await db_manager.update_order_status(order_id, "cancelled", updated_ts=now_ts)
                except Exception as e:
                    self.logger.error(
                        f"Failed to cancel stale order {order_id}: {e}",
                        order_id=order_id,
                        ticker=ticker
                    )

    def _get_price_reference(self, order: dict, market: dict) -> Optional[int]:
        """Get the appropriate market price reference for drift checks."""
        side = (order.get("side") or "").lower()
        action = (order.get("action") or "").lower()

        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        no_bid = market.get("no_bid")
        no_ask = market.get("no_ask")

        if side == "yes":
            return yes_ask if action == "buy" else yes_bid
        if side == "no":
            return no_ask if action == "buy" else no_bid
        return None

    async def _run_market_ingestion(self, db_manager: DatabaseManager, kalshi_client: KalshiClient):
        """Background task for market data ingestion."""
        while not self.shutdown_event.is_set():
            try:
                # Create a queue for market ingestion (though we're not using it in Beast Mode)
                market_queue = asyncio.Queue()
                # ✅ FIXED: Pass the shared database manager and kalshi_client
                await run_ingestion(db_manager, market_queue, kalshi_client=kalshi_client)
                await asyncio.sleep(300)  # Run every 5 minutes (slower to prevent 429s)
            except Exception as e:
                self.logger.error(f"Error in market ingestion: {e}")
                await asyncio.sleep(60)

    async def _run_trading_cycles(self, db_manager: DatabaseManager, kalshi_client: KalshiClient, xai_client: XAIClient, price_tracker=None, ws_manager=None):
        """Main Beast Mode trading cycles with Phase 3 enhancements."""
        cycle_count = 0

        while not self.shutdown_event.is_set():
            try:
                # Check safe mode first (from codex branch)
                if is_safe_mode_active():
                    self.logger.warning("🛑 Safe mode active - trading cycle paused")
                    await asyncio.sleep(60)
                    continue

                # Check risk cooldown (from main branch)
                cooldown_active, cooldown_state = is_risk_cooldown_active(db_manager.db_path)
                if cooldown_active and cooldown_state:
                    remaining = cooldown_state.cooldown_until - datetime.now()
                    remaining_seconds = max(0, int(remaining.total_seconds()))
                    self.logger.warning(
                        "🛑 Risk cooldown active",
                        cooldown_until=cooldown_state.cooldown_until.isoformat(),
                        violations=cooldown_state.violations,
                        remaining_seconds=remaining_seconds
                    )
                    await self._sleep_with_shutdown(remaining_seconds or 60)
                    continue

                # Check daily AI cost limits before starting cycle
                if not await self._check_daily_ai_limits(xai_client):
                    # Sleep until next day if limits reached
                    await self._sleep_until_next_day()
                    continue
                
                cycle_count += 1
                # Only log every 30 cycles (60 seconds worth) to avoid spam in high-frequency mode
                if cycle_count % 30 == 1:
                    self.logger.info(f"⚡ Beast Mode HIGH-FREQUENCY Cycle #{cycle_count} (2s intervals)")
                
                # Run the Beast Mode unified trading system
                results = await run_trading_job(
                    db_manager=db_manager,
                    kalshi_client=kalshi_client,
                    xai_client=xai_client
                )
                
                if results and results.total_positions > 0:
                    self.logger.info(
                        f"✅ HFT Cycle #{cycle_count} Complete - "
                        f"Positions: {results.total_positions}, "
                        f"Capital Used: ${results.total_capital_used:.0f} ({results.capital_efficiency:.1%}), "
                        f"Expected Return: {results.expected_annual_return:.1%}"
                    )
                # Don't log "no positions" every 2 seconds - too spammy

                # 🚀 PHASE 3: Record price snapshots periodically (every 10 cycles = 20 seconds)
                if price_tracker and cycle_count % 10 == 0:
                    try:
                        # Get active markets and record their prices
                        markets = await db_manager.get_eligible_markets(volume_min=200, max_days_to_expiry=365)
                        if markets:
                            # Record top 50 markets to avoid overhead
                            price_snapshots = []
                            for market in markets[:50]:
                                try:
                                    market_data = await kalshi_client.get_market(market.market_id)
                                    market_info = market_data.get('market', {})
                                    yes_price = market_info.get('yes_price', 50) / 100
                                    no_price = market_info.get('no_price', 50) / 100
                                    volume = market_info.get('volume', 0)
                                    price_snapshots.append((market.market_id, yes_price, no_price, volume))
                                except Exception:
                                    pass  # Skip markets that fail

                            if price_snapshots:
                                await price_tracker.batch_record_prices(price_snapshots)
                    except Exception as e:
                        pass  # Don't let price recording break trading

                # ⚡ HIGH-FREQUENCY MODE: Wait for next cycle (2 seconds for rapid monitoring and 0.1s precision)
                await asyncio.sleep(self.scan_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in trading cycle #{cycle_count}: {e}")
                await asyncio.sleep(2)  # Quick recovery for high-frequency trading

    async def _sleep_with_shutdown(self, total_seconds: float, chunk_size: int = 60):
        """Sleep in chunks while allowing graceful shutdown."""
        remaining = max(0, total_seconds)
        while remaining > 0 and not self.shutdown_event.is_set():
            current_chunk = min(chunk_size, remaining)
            await asyncio.sleep(current_chunk)
            remaining -= current_chunk

    async def _check_daily_ai_limits(self, xai_client: XAIClient) -> bool:
        """
        Check if we should continue trading based on daily AI cost limits.
        Returns True if we can continue, False if we should pause.
        """
        if not settings.trading.enable_daily_cost_limiting:
            return True
        
        # Check daily tracker in xAI client
        if hasattr(xai_client, 'daily_tracker') and xai_client.daily_tracker.is_exhausted:
            self.logger.warning(
                "🚫 Daily AI cost limit reached - trading paused",
                daily_cost=xai_client.daily_tracker.total_cost,
                daily_limit=xai_client.daily_tracker.daily_limit,
                requests_today=xai_client.daily_tracker.request_count
            )
            return False
        
        return True

    async def _sleep_until_next_day(self):
        """Sleep until the next day (midnight) when daily limits reset."""
        if not settings.trading.sleep_when_limit_reached:
            # Just sleep for a normal cycle if sleep is disabled
            await asyncio.sleep(60)
            return
        
        # Calculate time until next day
        now = datetime.now()
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_next_day = (next_day - now).total_seconds()
        
        # Ensure we don't sleep for more than 24 hours (safety check)
        max_sleep = 24 * 60 * 60  # 24 hours
        sleep_time = min(seconds_until_next_day, max_sleep)
        
        if sleep_time > 0:
            hours_to_sleep = sleep_time / 3600
            self.logger.info(
                f"💤 Sleeping until next day to reset AI limits - {hours_to_sleep:.1f} hours"
            )
            
            # Sleep in chunks to allow for graceful shutdown
            chunk_size = 300  # 5 minutes per chunk
            while sleep_time > 0 and not self.shutdown_event.is_set():
                current_chunk = min(chunk_size, sleep_time)
                await asyncio.sleep(current_chunk)
                sleep_time -= current_chunk
            
            self.logger.info("🌅 Daily AI limits reset - resuming trading")
        else:
            # Safety fallback
            await asyncio.sleep(60)

    async def _sleep_with_shutdown(self, sleep_seconds: int):
        """Sleep in chunks to allow graceful shutdown."""
        if sleep_seconds <= 0:
            return
        chunk_size = 60
        remaining = sleep_seconds
        while remaining > 0 and not self.shutdown_event.is_set():
            current_chunk = min(chunk_size, remaining)
            await asyncio.sleep(current_chunk)
            remaining -= current_chunk

    async def _run_position_tracking(self, db_manager: DatabaseManager, kalshi_client: KalshiClient):
        """Background task for position tracking and exit strategies."""
        while not self.shutdown_event.is_set():
            try:
                # ✅ FIXED: Pass the shared database manager
                await run_tracking(db_manager)
                await asyncio.sleep(2)  # ⚡ ULTRA-HIGH-FREQUENCY: Check positions every 2 seconds for maximum exit speed
            except Exception as e:
                self.logger.error(f"Error in position tracking: {e}")
                await asyncio.sleep(30)

    async def _run_performance_evaluation(self, db_manager: DatabaseManager):
        """Background task for performance evaluation."""
        while not self.shutdown_event.is_set():
            try:
                await run_evaluation()
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in performance evaluation: {e}")
                await asyncio.sleep(300)

    async def run(self):
        """Main entry point for Beast Mode Bot."""
        if self.dashboard_mode:
            await self.run_dashboard_mode()
        else:
            await self.run_trading_mode()


async def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Beast Mode Trading Bot 🚀 - Advanced Multi-Strategy Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python beast_mode_bot.py              # Paper trading mode
  python beast_mode_bot.py --live       # Live trading mode  
  python beast_mode_bot.py --dashboard  # Live dashboard mode
  python beast_mode_bot.py --live --log-level DEBUG  # Live mode with debug logs

Beast Mode Features:
  • Market Making (40% allocation) - Profit from spreads
  • Directional Trading (50% allocation) - AI predictions with portfolio optimization
  • Arbitrage Detection (10% allocation) - Cross-market opportunities
  • No time restrictions - Trade any deadline with dynamic exits
  • Kelly Criterion portfolio optimization
  • Real-time risk management and rebalancing
  • Cost controls and budget management
        """
    )
    
    parser.add_argument(
        "--live", 
        action="store_true", 
        help="Run in LIVE trading mode (default: paper trading)"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Run in live dashboard mode for monitoring"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level (default: INFO)"
    )
    parser.add_argument(
        "--force-live",
        action="store_true",
        help="Override live trading safety check (use with caution)"
    )
    parser.add_argument(
        "--scan-interval",
        type=int,
        default=60,
        help="Trading cycle scan interval in seconds (default: 60)"
    )

    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = get_trading_logger("beast_mode_bot")

    async def check_live_readiness() -> Tuple[bool, str]:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        async with aiosqlite.connect(db_manager.db_path) as db:
            cursor = await db.execute("""
                SELECT ready_for_live, rolling_win_rate, rolling_max_drawdown, rolling_sharpe, timestamp
                FROM analysis_reports
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            latest = await cursor.fetchone()

        if not latest:
            return False, "No analysis report available"

        ready_for_live = bool(latest[0])
        summary = (
            f"ready_for_live={ready_for_live}, "
            f"win_rate={latest[1]:.1%}, "
            f"max_drawdown={latest[2]:.1%}, "
            f"sharpe={latest[3]:.2f}, "
            f"reported_at={latest[4]}"
        )
        return ready_for_live, summary

    if args.live and not args.force_live and not args.dashboard:
        ready_for_live, reason = await check_live_readiness()
        if not ready_for_live:
            logger.error("Live trading blocked", reason=reason)
            print(f"🚫 LIVE TRADING BLOCKED: {reason}")
            return
    elif args.live and args.force_live and not args.dashboard:
        logger.warning("Live trading override enabled", reason="--force-live")
    
    # Warn about live mode
    if args.live and not args.dashboard:
        print("⚠️  WARNING: LIVE TRADING MODE ENABLED")
        print("💰 This will use real money and place actual trades!")
        print("🚀 LIVE TRADING MODE CONFIRMED")
    
    # Create and run Beast Mode Bot
    bot = BeastModeBot(
        live_mode=args.live,
        dashboard_mode=args.dashboard,
        scan_interval_seconds=args.scan_interval
    )
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Beast Mode Bot stopped by user")
    except Exception as e:
        print(f"❌ Beast Mode Bot error: {e}")
        raise
