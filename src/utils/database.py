
hi

2:41 PM
Hi there! How can I help you today?


""" Database manager for the Kalshi trading system. """ import aiosqlite import json from dataclasses import dataclass, asdict from datetime import datetime, timedelta from pathlib import Path from typing import Optional, List, Dict from src.utils.logging_setup import TradingLoggerMixin @datacla

pasted

please fix code

2:41 PM
I can see there are git merge conflicts in this file. Let me fix them by resolving the conflicts and keeping the best parts of both versions.


Creating fixed database.py with merge conflicts resolved
database.py

Presented file
I've fixed the merge conflicts in your code. The main changes were:

Removed git merge conflict markers (<<<<<<< codex/add-failure-counter-and-safe-mode-to-databasemanager, =======, >>>>>>> main)
Kept the safe mode functionality from the codex branch (the _load_state, _save_state, is_safe_mode, get_safe_mode_state, record_failure, and reset_safe_mode methods)
Kept the cleaner _run_migrations method from the main branch (which was more consolidated)
Kept the close method and __main__ block from the main branch
Fixed the duplicate close method issue - there was one defined twice
Database
PY 

""" Database manager for the Kalshi trading system. """ import aiosqlite import json from dataclasses import dataclass, asdict from datetime import datetime, timedelta from pathlib import Path from typing import Optional, List, Dict from src.utils.logging_setup import TradingLoggerMixin @datacla

pasted

same for this

2:45 PM
I can see another git merge conflict at the end of this file. Let me fix it:


Creating fixed database.py with merge conflict resolved - keeping the close method and __main__ block from main branch
database_fixed.py

Presented file
Fixed! The merge conflict was at the end of the file. I removed the conflict markers and kept:

The close() method from the main branch
The if __name__ == "__main__": block for standalone database initialization
This version also includes the stale market data filtering logic from the codex/implement-last_updated-timestamps-and-filtering branch in the get_eligible_markets() method (with max_recency_seconds = 30).

Database fixed
PY 

""" Unified Advanced Trading System - The Beast Mode 🚀 This system orchestrates all cutting-edge strategies: 1. Market Making Strategy (limit orders for spreads) 2. Advanced Portfolio Optimization (Kelly Criterion Extension) 3. Risk Parity Allocation (equal risk, not equal capital) 4. Dynamic Exit

pasted

fix

2:57 PM
I can see merge conflicts in this file. Let me fix them:


1 step

Remove existing file to recreate it


Creating fixed unified_trading_system.py with merge conflicts resolved

#!/usr/bin/env python3 """ Beast Mode Trading Bot 🚀 Main entry point for the Unified Advanced Trading System that orchestrates: - Market Making Strategy (40% allocation) - Directional Trading with Portfolio Optimization (50% allocation) - Arbitrage Detection (10% allocation) Features: - No time

pasted


""" XAI client for AI-powered trading decisions. Interfaces with Grok models through xAI REST API (OpenAI-compatible) for market analysis and trading strategies. """ import asyncio import json import time from typing import Dict, List, Optional, Any, Union, Tuple from dataclasses import dataclass f

pasted


""" Trade Execution Job This job takes a position and executes it as a trade. """ import asyncio import uuid from datetime import datetime from typing import Optional, Dict from src.utils.database import DatabaseManager, Position from src.utils.logging_setup import get_trading_logger from src.util

pasted

fix ALL

3:04 PM

Identified and resolved merge conflicts across three files.


I'll fix all three files with merge conflicts.


4 steps

Creating fixed execute.py with merge conflicts resolved - combining notification support with fill verification
execute.py

I also realized I need to complete the unified_trading_system.py file that got cut off.

Now let me present all the fixed files:


4 steps

Check if unified_trading_system.py was properly created



Diagnosed file creation failure and resolved implementation.

Let me complete the unified_trading_system.py file which got truncated:


4 steps

Presented 5 files

Resolved merge conflicts and synthesized comprehensive changes.

All files fixed! Here's a summary of the merge conflict resolutions:

1. beast_mode_bot.py
Fixed the _run_market_ingestion method to pass kalshi_client to run_ingestion()
Kept the slower 300-second (5 minute) ingestion interval to prevent 429 rate limit errors
2. xai_client.py
Fixed the search() method to use REST API chat completion instead of the gRPC SDK
Added the search cache initialization in __init__
Kept the simpler approach while preserving query optimization and caching functionality
3. execute.py
Combined notification support (from one branch) with fill verification via backoff (from the other)
Order flow now: place order → fetch fills with backoff → verify fill → send notifications
Falls back to entry price if fills aren't confirmed, but still sends notifications
4. unified_trading_system.py
Combined market_data_max_age_seconds config and risk_cooldown_minutes config
Removed duplicate stale market filtering (now handled in get_eligible_markets)
Simplified the strategy execution while keeping all functionality
5. database_fixed.py
Kept safe mode functionality (_load_state, _save_state, is_safe_mode, etc.)
Kept the stale market filtering in get_eligible_markets()
Included the close() method and __main__ block
Beast mode bot
PY 
Xai client
PY 
Execute
PY 
Unified trading system
PY 
Database fixed
PY 
1767817178838_image.png

#!/usr/bin/env python3 """ Beast Mode Trading Bot 🚀 Main entry point for the Unified Advanced Trading System that orchestrates: - Market Making Strategy (40% allocation) - Directional Trading with Portfolio Optimization (50% allocation) - Arbitrage Detection (10% allocation) Features: - No time

pasted


""" Database manager for the Kalshi trading system. """ import aiosqlite import json from dataclasses import dataclass, asdict from datetime import datetime, timedelta from pathlib import Path from typing import Optional, List, Dict from src.utils.logging_setup import TradingLoggerMixin @datacla

pasted

many pr's codex has done but before i updated your changes, help me fix all these pr's please, thank you!!!! there many be multipe of same

3:19 PM

Analyzed merge conflicts across multiple files and reconciled divergent code branches.









I see PR #20 has conflicts in both beast_mode_bot.py and database.py. Let me fix both files by combining the features from both branches.


Hide steps

Creating fixed beast_mode_bot.py - combining Order sync features from codex branch with risk_cooldown from main
beast_mode_bot_pr20.py

Reconciled conflicting code branches to preserve all functionality.


Creating fixed database.py - combining Order dataclass and methods from codex with close() and __main__ from main
database_pr20.py

Prepared to present files for user review.


Presented 2 files

Resolved conflicting files across multiple pull requests.

Fixed PR #20! Here's what I merged:

beast_mode_bot_pr20.py
Combined both branches:

✅ From codex branch: Order import, _sync_startup_state(), _normalize_order(), _parse_timestamp(), _cancel_stale_orders(), _get_price_reference(), orders table check in _ensure_database_ready()
✅ From main branch: is_risk_cooldown_active import and risk cooldown check in _run_trading_cycles()
✅ Fixed trailing whitespace on raise
database_pr20.py
Combined both branches:

✅ From codex branch: Order dataclass, upsert_orders(), update_order_status(), orders table creation
✅ From main branch: close() method and if __name__ == "__main__": block
To use these files: Simply rename them to replace the originals:

beast_mode_bot_pr20.py → beast_mode_bot.py
database_pr20.py → src/utils/database.py
Do you have more PRs with conflicts to fix? If so, please share them and I'll resolve those too!

Beast mode bot pr20
PY 
Database pr20
PY 






Claude is AI and can make mistakes. Please double-check responses.
Database pr20 · PY
Copy

"""
Database manager for the Kalshi trading system.
"""

import aiosqlite
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from src.utils.logging_setup import TradingLoggerMixin


@dataclass
class Market:
    """Represents a market in the database."""
    market_id: str
    title: str
    yes_price: float
    no_price: float
    volume: int
    expiration_ts: int
    category: str
    status: str
    last_updated: datetime
    has_position: bool = False

@dataclass
class Position:
    """Represents a trading position."""
    market_id: str
    side: str  # "YES" or "NO"
    entry_price: float
    quantity: int
    timestamp: datetime
    rationale: Optional[str] = None
    confidence: Optional[float] = None
    live: bool = False
    status: str = "open"  # open, closed, pending
    id: Optional[int] = None
    strategy: Optional[str] = None  # Strategy that created this position
    
    # Enhanced exit strategy fields
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    max_hold_hours: Optional[int] = None  # Maximum hours to hold position
    target_confidence_change: Optional[float] = None  # Exit if confidence drops by this amount

@dataclass
class Order:
    """Represents an order synced from Kalshi."""
    order_id: str
    ticker: str
    status: str
    side: Optional[str] = None
    action: Optional[str] = None
    type: Optional[str] = None
    yes_price: Optional[int] = None
    no_price: Optional[int] = None
    count: Optional[int] = None
    remaining_count: Optional[int] = None
    created_ts: Optional[int] = None
    updated_ts: Optional[int] = None
    client_order_id: Optional[str] = None
    expiration_ts: Optional[int] = None
    last_synced: Optional[datetime] = None

@dataclass
class TradeLog:
    """Represents a closed trade for logging and analysis."""
    market_id: str
    side: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    entry_timestamp: datetime
    exit_timestamp: datetime
    rationale: str
    strategy: Optional[str] = None  # Strategy that created this trade
    id: Optional[int] = None

@dataclass
class LLMQuery:
    """Represents an LLM query and response for analysis."""
    timestamp: datetime
    strategy: str  # Which strategy made the query
    query_type: str  # Type of query (market_analysis, movement_prediction, etc.)
    market_id: Optional[str]  # Market being analyzed (if applicable)
    prompt: str  # The prompt sent to LLM
    response: str  # LLM response
    tokens_used: Optional[int] = None  # Tokens consumed
    cost_usd: Optional[float] = None  # Cost in USD
    confidence_extracted: Optional[float] = None  # Confidence if extracted
    decision_extracted: Optional[str] = None  # Decision if extracted
    id: Optional[int] = None


class DatabaseManager(TradingLoggerMixin):
    """Manages database operations for the trading system."""

    def __init__(
        self,
        db_path: str = "trading_system.db",
        state_path: str = "trading_state.json",
        failure_threshold: int = 3
    ):
        """Initialize database connection."""
        self.db_path = db_path
        self.state_path = Path(state_path)
        self.failure_threshold = failure_threshold
        self.logger.info("Initializing database manager", db_path=db_path)

    async def initialize(self) -> None:
        """Initialize database schema and run migrations."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await self._run_migrations(db)
            await db.commit()
        self.logger.info("Database initialized successfully")

    def _load_state(self) -> Dict:
        if not self.state_path.exists():
            return {
                "failure_count": 0,
                "safe_mode": False,
                "last_failure_at": None,
                "last_failure_reason": None,
                "manual_reset_at": None
            }
        try:
            return json.loads(self.state_path.read_text())
        except json.JSONDecodeError:
            self.logger.error("Failed to decode trading state file; resetting state", state_path=str(self.state_path))
            return {
                "failure_count": 0,
                "safe_mode": False,
                "last_failure_at": None,
                "last_failure_reason": None,
                "manual_reset_at": None
            }

    def _save_state(self, state: Dict) -> None:
        self.state_path.write_text(json.dumps(state, indent=2, sort_keys=True))

    def is_safe_mode(self) -> bool:
        state = self._load_state()
        return bool(state.get("safe_mode", False))

    def get_safe_mode_state(self) -> Dict:
        return self._load_state()

    def record_failure(self, reason: str) -> None:
        state = self._load_state()
        state["failure_count"] = int(state.get("failure_count", 0)) + 1
        state["last_failure_at"] = datetime.now().isoformat()
        state["last_failure_reason"] = reason
        if state["failure_count"] >= self.failure_threshold:
            if not state.get("safe_mode"):
                self.logger.warning(
                    "Safe mode enabled due to repeated failures",
                    failure_count=state["failure_count"],
                    failure_threshold=self.failure_threshold,
                    reason=reason
                )
            state["safe_mode"] = True
        self._save_state(state)

    def reset_safe_mode(self) -> None:
        state = self._load_state()
        state["failure_count"] = 0
        state["safe_mode"] = False
        state["manual_reset_at"] = datetime.now().isoformat()
        self._save_state(state)
        self.logger.info("Safe mode reset manually", state_path=str(self.state_path))

    async def _migrate_existing_strategy_data(self, db: aiosqlite.Connection) -> None:
        """Migrate existing position data to include strategy information."""
        try:
            # Update positions based on rationale patterns
            await db.execute("""
                UPDATE positions 
                SET strategy = 'quick_flip_scalping' 
                WHERE strategy IS NULL AND rationale LIKE 'QUICK FLIP:%'
            """)
            
            await db.execute("""
                UPDATE positions 
                SET strategy = 'portfolio_optimization' 
                WHERE strategy IS NULL AND rationale LIKE 'Portfolio optimization allocation:%'
            """)
            
            await db.execute("""
                UPDATE positions 
                SET strategy = 'market_making' 
                WHERE strategy IS NULL AND (
                    rationale LIKE '%market making%' OR 
                    rationale LIKE '%spread profit%'
                )
            """)
            
            await db.execute("""
                UPDATE positions 
                SET strategy = 'directional_trading' 
                WHERE strategy IS NULL AND (
                    rationale LIKE 'High-confidence%' OR
                    rationale LIKE '%near-expiry%' OR
                    rationale LIKE '%decision%'
                )
            """)
            
            # Update trade_logs similarly
            await db.execute("""
                UPDATE trade_logs 
                SET strategy = 'quick_flip_scalping' 
                WHERE strategy IS NULL AND rationale LIKE 'QUICK FLIP:%'
            """)
            
            await db.execute("""
                UPDATE trade_logs 
                SET strategy = 'portfolio_optimization' 
                WHERE strategy IS NULL AND rationale LIKE 'Portfolio optimization allocation:%'
            """)
            
            await db.execute("""
                UPDATE trade_logs 
                SET strategy = 'market_making' 
                WHERE strategy IS NULL AND (
                    rationale LIKE '%market making%' OR 
                    rationale LIKE '%spread profit%'
                )
            """)
            
            await db.execute("""
                UPDATE trade_logs 
                SET strategy = 'directional_trading' 
                WHERE strategy IS NULL AND (
                    rationale LIKE 'High-confidence%' OR
                    rationale LIKE '%near-expiry%' OR
                    rationale LIKE '%decision%'
                )
            """)
            
            self.logger.info("Migrated existing position/trade data with strategy information")
            
        except Exception as e:
            self.logger.error(f"Error migrating existing strategy data: {e}")

    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """Create all database tables."""
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS markets (
                market_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                yes_price REAL NOT NULL,
                no_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                expiration_ts INTEGER NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                has_position BOOLEAN NOT NULL DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                rationale TEXT,
                confidence REAL,
                live BOOLEAN NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'open',
                strategy TEXT,
                stop_loss_price REAL,
                take_profit_price REAL,
                max_hold_hours INTEGER,
                target_confidence_change REAL,
                UNIQUE(market_id, side)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                pnl REAL NOT NULL,
                entry_timestamp TEXT NOT NULL,
                exit_timestamp TEXT NOT NULL,
                rationale TEXT,
                strategy TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                status TEXT NOT NULL,
                side TEXT,
                action TEXT,
                type TEXT,
                yes_price INTEGER,
                no_price INTEGER,
                count INTEGER,
                remaining_count INTEGER,
                created_ts INTEGER,
                updated_ts INTEGER,
                client_order_id TEXT,
                expiration_ts INTEGER,
                last_synced TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS market_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                analysis_timestamp TEXT NOT NULL,
                decision_action TEXT NOT NULL,
                confidence REAL,
                cost_usd REAL NOT NULL,
                analysis_type TEXT NOT NULL DEFAULT 'standard'
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_cost_tracking (
                date TEXT PRIMARY KEY,
                total_ai_cost REAL NOT NULL DEFAULT 0.0,
                analysis_count INTEGER NOT NULL DEFAULT 0,
                decision_count INTEGER NOT NULL DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS llm_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                strategy TEXT NOT NULL,
                query_type TEXT NOT NULL,
                market_id TEXT,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                tokens_used INTEGER,
                cost_usd REAL,
                confidence_extracted REAL,
                decision_extracted TEXT
            )
        """)

        # Add analysis_reports table for performance tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                health_score REAL NOT NULL,
                critical_issues INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                action_items INTEGER DEFAULT 0,
                report_file TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_market_analyses_market_id ON market_analyses(market_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_market_analyses_timestamp ON market_analyses(analysis_timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_daily_cost_date ON daily_cost_tracking(date)")
        
        self.logger.info("Tables created or already exist.")

    async def _run_migrations(self, db: aiosqlite.Connection) -> None:
        """Run database migrations to ensure schema is up to date."""
        try:
            cursor = await db.execute("PRAGMA table_info(positions)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'strategy' not in column_names:
                self.logger.info("Adding strategy column to positions table")
                await db.execute("ALTER TABLE positions ADD COLUMN strategy TEXT")

            if 'stop_loss_price' not in column_names:
                await db.execute("ALTER TABLE positions ADD COLUMN stop_loss_price REAL")
                self.logger.info("Added stop_loss_price column to positions table")

            if 'take_profit_price' not in column_names:
                await db.execute("ALTER TABLE positions ADD COLUMN take_profit_price REAL")
                self.logger.info("Added take_profit_price column to positions table")

            if 'max_hold_hours' not in column_names:
                await db.execute("ALTER TABLE positions ADD COLUMN max_hold_hours INTEGER")
                self.logger.info("Added max_hold_hours column to positions table")

            if 'target_confidence_change' not in column_names:
                await db.execute("ALTER TABLE positions ADD COLUMN target_confidence_change REAL")
                self.logger.info("Added target_confidence_change column to positions table")

            cursor = await db.execute("PRAGMA table_info(trade_logs)")
            columns = await cursor.fetchall()
            trade_column_names = [col[1] for col in columns]

            if 'strategy' not in trade_column_names:
                self.logger.info("Adding strategy column to trade_logs table")
                await db.execute("ALTER TABLE trade_logs ADD COLUMN strategy TEXT")

            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_queries'")
            table_exists = await cursor.fetchone()

            if not table_exists:
                self.logger.info("Creating llm_queries table")
                await db.execute("""
                    CREATE TABLE llm_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        query_type TEXT NOT NULL,
                        market_id TEXT,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        tokens_used INTEGER,
                        cost_usd REAL,
                        confidence_extracted REAL,
                        decision_extracted TEXT
                    )
                """)

            await self._migrate_existing_strategy_data(db)

            await db.commit()

        except Exception as e:
            self.logger.error(f"Error running migrations: {e}")

    async def upsert_markets(self, markets: List[Market]):
        """
        Upsert a list of markets into the database.
        
        Args:
            markets: A list of Market dataclass objects.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # SQLite STRFTIME arguments needs to be a string
            # and asdict converts datetime to datetime object
            # so we need to convert it to string manually
            market_dicts = []
            for m in markets:
                market_dict = asdict(m)
                market_dict['last_updated'] = m.last_updated.isoformat()
                market_dicts.append(market_dict)

            await db.executemany("""
                INSERT INTO markets (market_id, title, yes_price, no_price, volume, expiration_ts, category, status, last_updated, has_position)
                VALUES (:market_id, :title, :yes_price, :no_price, :volume, :expiration_ts, :category, :status, :last_updated, :has_position)
                ON CONFLICT(market_id) DO UPDATE SET
                    title=excluded.title,
                    yes_price=excluded.yes_price,
                    no_price=excluded.no_price,
                    volume=excluded.volume,
                    expiration_ts=excluded.expiration_ts,
                    category=excluded.category,
                    status=excluded.status,
                    last_updated=excluded.last_updated,
                    has_position=excluded.has_position
            """, market_dicts)
            await db.commit()
            self.logger.info(f"Upserted {len(markets)} markets.")

    async def upsert_orders(self, orders: List[Order]):
        """
        Upsert a list of orders into the database.

        Args:
            orders: A list of Order dataclass objects.
        """
        if not orders:
            return

        async with aiosqlite.connect(self.db_path) as db:
            order_dicts = []
            for order in orders:
                order_dict = asdict(order)
                order_dict['last_synced'] = (
                    order.last_synced.isoformat()
                    if order.last_synced
                    else datetime.utcnow().isoformat()
                )
                order_dicts.append(order_dict)

            await db.executemany("""
                INSERT INTO orders (
                    order_id, ticker, status, side, action, type, yes_price, no_price, count,
                    remaining_count, created_ts, updated_ts, client_order_id, expiration_ts, last_synced
                )
                VALUES (
                    :order_id, :ticker, :status, :side, :action, :type, :yes_price, :no_price, :count,
                    :remaining_count, :created_ts, :updated_ts, :client_order_id, :expiration_ts, :last_synced
                )
                ON CONFLICT(order_id) DO UPDATE SET
                    ticker=excluded.ticker,
                    status=excluded.status,
                    side=excluded.side,
                    action=excluded.action,
                    type=excluded.type,
                    yes_price=excluded.yes_price,
                    no_price=excluded.no_price,
                    count=excluded.count,
                    remaining_count=excluded.remaining_count,
                    created_ts=excluded.created_ts,
                    updated_ts=excluded.updated_ts,
                    client_order_id=excluded.client_order_id,
                    expiration_ts=excluded.expiration_ts,
                    last_synced=excluded.last_synced
            """, order_dicts)
            await db.commit()
            self.logger.info(f"Upserted {len(orders)} orders.")

    async def update_order_status(self, order_id: str, status: str, updated_ts: Optional[int] = None):
        """Update the status (and optionally updated_ts) for a specific order."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE orders
                SET status = ?, updated_ts = COALESCE(?, updated_ts), last_synced = ?
                WHERE order_id = ?
            """, (status, updated_ts, datetime.utcnow().isoformat(), order_id))
            await db.commit()
            self.logger.info(f"Updated order {order_id} status to {status}.")

    async def get_eligible_markets(self, volume_min: int, max_days_to_expiry: int) -> List[Market]:
        """
        Get markets that are eligible for trading.

        Args:
            volume_min: Minimum trading volume.
            max_days_to_expiry: Maximum days to expiration.
        
        Returns:
            A list of eligible markets.
        """
        now = datetime.now()
        now_ts = int(now.timestamp())
        max_expiry_ts = now_ts + (max_days_to_expiry * 24 * 60 * 60)
        max_recency_seconds = 30

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM markets
                WHERE
                    volume >= ? AND
                    expiration_ts > ? AND
                    expiration_ts <= ? AND
                    status = 'active' AND
                    has_position = 0
            """, (volume_min, now_ts, max_expiry_ts))
            rows = await cursor.fetchall()
            
            markets = []
            for row in rows:
                market_dict = dict(row)
                market_dict['last_updated'] = datetime.fromisoformat(market_dict['last_updated'])
                market = Market(**market_dict)
                age_seconds = (now - market.last_updated).total_seconds()
                if age_seconds > max_recency_seconds:
                    self.logger.warning(
                        "Skipping stale market data",
                        market_id=market.market_id,
                        age_seconds=round(age_seconds, 2),
                        last_updated=market.last_updated.isoformat(),
                    )
                    continue
                markets.append(market)
            return markets

    async def get_active_markets(self) -> List[Market]:
        """
        Get all active markets from the database.

        Returns:
            List of active markets
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM markets WHERE status = 'active'
            """)
            rows = await cursor.fetchall()

            markets = []
            for row in rows:
                market_dict = dict(row)
                market_dict['last_updated'] = datetime.fromisoformat(market_dict['last_updated'])
                markets.append(Market(**market_dict))
            return markets

    async def get_markets_with_positions(self) -> set[str]:
        """
        Returns a set of market IDs that have associated open positions.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT DISTINCT market_id FROM positions WHERE status IN ('open', 'pending')
            """)
            rows = await cursor.fetchall()
            return {row[0] for row in rows}

    async def is_position_opening_for_market(self, market_id: str) -> bool:
        """
        Checks if a position is currently being opened for a given market.
        This is to prevent race conditions where multiple workers try to open a position for the same market.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT market_id FROM positions WHERE market_id = ? AND status = 'pending' LIMIT 1
            """, (market_id,))
            row = await cursor.fetchone()
            return row is not None

    async def get_open_non_live_positions(self) -> List[Position]:
        """
        Get all positions that are open and not live.
        
        Returns:
            A list of Position objects.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM positions WHERE status = 'open' AND live = 0")
            rows = await cursor.fetchall()
            
            positions = []
            for row in rows:
                position_dict = dict(row)
                position_dict['timestamp'] = datetime.fromisoformat(position_dict['timestamp'])
                positions.append(Position(**position_dict))
            return positions

    async def get_open_live_positions(self) -> List[Position]:
        """
        Get all positions that are open and live.
        
        Returns:
            A list of Position objects.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM positions WHERE status = 'open' AND live = 1")
            rows = await cursor.fetchall()
            
            positions = []
            for row in rows:
                position_dict = dict(row)
                position_dict['timestamp'] = datetime.fromisoformat(position_dict['timestamp'])
                positions.append(Position(**position_dict))
            return positions

    async def update_position_status(self, position_id: int, status: str):
        """
        Updates the status of a position.

        Args:
            position_id: The id of the position to update.
            status: The new status ('closed', 'voided').
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE positions SET status = ? WHERE id = ?
            """, (status, position_id))
            await db.commit()
            self.logger.info(f"Updated position {position_id} status to {status}.")

    async def get_position_by_market_id(self, market_id: str) -> Optional[Position]:
        """
        Get a position by market ID.
        
        Args:
            market_id: The ID of the market.
            
        Returns:
            A Position object if found, otherwise None.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM positions WHERE market_id = ? AND status = 'open' LIMIT 1", (market_id,))
            row = await cursor.fetchone()
            if row:
                position_dict = dict(row)
                position_dict['timestamp'] = datetime.fromisoformat(position_dict['timestamp'])
                return Position(**position_dict)
            return None

    async def get_position_by_market_and_side(self, market_id: str, side: str) -> Optional[Position]:
        """
        Get a position by market ID and side.
        
        Args:
            market_id: The ID of the market.
            side: The side of the position ('YES' or 'NO').

        Returns:
            A Position object if found, otherwise None.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM positions WHERE market_id = ? AND side = ? AND status = 'open'", 
                (market_id, side)
            )
            row = await cursor.fetchone()
            if row:
                position_dict = dict(row)
                position_dict['timestamp'] = datetime.fromisoformat(position_dict['timestamp'])
                return Position(**position_dict)
            return None

    async def add_trade_log(self, trade_log: TradeLog) -> None:
        """
        Add a trade log entry.
        
        Args:
            trade_log: The trade log to add.
        """
        trade_dict = asdict(trade_log)
        trade_dict['entry_timestamp'] = trade_log.entry_timestamp.isoformat()
        trade_dict['exit_timestamp'] = trade_log.exit_timestamp.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO trade_logs (market_id, side, entry_price, exit_price, quantity, pnl, entry_timestamp, exit_timestamp, rationale, strategy)
                VALUES (:market_id, :side, :entry_price, :exit_price, :quantity, :pnl, :entry_timestamp, :exit_timestamp, :rationale, :strategy)
            """, trade_dict)
            await db.commit()
            self.logger.info(f"Added trade log for market {trade_log.market_id}.")

    async def get_performance_by_strategy(self) -> Dict[str, Dict]:
        """
        Get performance metrics broken down by strategy.
        
        Returns:
            Dictionary with strategy names as keys and performance metrics as values.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Check if strategy column exists in trade_logs
            cursor = await db.execute("PRAGMA table_info(trade_logs)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            has_strategy_in_trades = 'strategy' in column_names
            
            completed_stats = []
            
            if has_strategy_in_trades:
                # Get stats from completed trades (trade_logs)
                cursor = await db.execute("""
                    SELECT 
                        strategy,
                        COUNT(*) as trade_count,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade
                    FROM trade_logs 
                    WHERE strategy IS NOT NULL
                    GROUP BY strategy
                """)
                completed_stats = await cursor.fetchall()
            else:
                # If no strategy column, create a generic entry
                cursor = await db.execute("""
                    SELECT 
                        'legacy_trades' as strategy,
                        COUNT(*) as trade_count,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade
                    FROM trade_logs
                """)
                result = await cursor.fetchone()
                if result and result['trade_count'] > 0:
                    completed_stats = [result]
            
            # Check if strategy column exists in positions
            cursor = await db.execute("PRAGMA table_info(positions)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            has_strategy_in_positions = 'strategy' in column_names
            
            open_stats = []
            
            if has_strategy_in_positions:
                # Get current open positions by strategy
                cursor = await db.execute("""
                    SELECT 
                        strategy,
                        COUNT(*) as open_positions,
                        SUM(quantity * entry_price) as capital_deployed
                    FROM positions 
                    WHERE status = 'open' AND strategy IS NOT NULL
                    GROUP BY strategy
                """)
                open_stats = await cursor.fetchall()
            else:
                # If no strategy column, create a generic entry
                cursor = await db.execute("""
                    SELECT 
                        'legacy_positions' as strategy,
                        COUNT(*) as open_positions,
                        SUM(quantity * entry_price) as capital_deployed
                    FROM positions 
                    WHERE status = 'open'
                """)
                result = await cursor.fetchone()
                if result and result['open_positions'] > 0:
                    open_stats = [result]
            
            # Combine the results
            performance = {}
            
            # Add completed trade stats
            for row in completed_stats:
                strategy = row['strategy'] or 'unknown'
                win_rate = (row['winning_trades'] / row['trade_count']) * 100 if row['trade_count'] > 0 else 0
                
                performance[strategy] = {
                    'completed_trades': row['trade_count'],
                    'total_pnl': row['total_pnl'],
                    'avg_pnl_per_trade': row['avg_pnl'],
                    'win_rate_pct': win_rate,
                    'winning_trades': row['winning_trades'],
                    'losing_trades': row['losing_trades'],
                    'best_trade': row['best_trade'],
                    'worst_trade': row['worst_trade'],
                    'open_positions': 0,
                    'capital_deployed': 0.0
                }
            
            # Add open position stats
            for row in open_stats:
                strategy = row['strategy'] or 'unknown'
                if strategy not in performance:
                    performance[strategy] = {
                        'completed_trades': 0,
                        'total_pnl': 0.0,
                        'avg_pnl_per_trade': 0.0,
                        'win_rate_pct': 0.0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'best_trade': 0.0,
                        'worst_trade': 0.0,
                        'open_positions': 0,
                        'capital_deployed': 0.0
                    }
                
                performance[strategy]['open_positions'] = row['open_positions']
                performance[strategy]['capital_deployed'] = row['capital_deployed']
            
            return performance

    async def log_llm_query(self, llm_query: LLMQuery) -> None:
        """Log an LLM query and response for analysis."""
        try:
            query_dict = asdict(llm_query)
            query_dict['timestamp'] = llm_query.timestamp.isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO llm_queries (
                        timestamp, strategy, query_type, market_id, prompt, response,
                        tokens_used, cost_usd, confidence_extracted, decision_extracted
                    ) VALUES (
                        :timestamp, :strategy, :query_type, :market_id, :prompt, :response,
                        :tokens_used, :cost_usd, :confidence_extracted, :decision_extracted
                    )
                """, query_dict)
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging LLM query: {e}")

    async def get_llm_queries(
        self, 
        strategy: Optional[str] = None,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[LLMQuery]:
        """Get recent LLM queries, optionally filtered by strategy."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Check if llm_queries table exists
                cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_queries'")
                table_exists = await cursor.fetchone()
                
                if not table_exists:
                    self.logger.info("LLM queries table doesn't exist yet - will be created on first query")
                    return []
                
                if strategy:
                    cursor = await db.execute("""
                        SELECT * FROM llm_queries 
                        WHERE strategy = ? AND timestamp >= ?
                        ORDER BY timestamp DESC LIMIT ?
                    """, (strategy, cutoff_time.isoformat(), limit))
                else:
                    cursor = await db.execute("""
                        SELECT * FROM llm_queries 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC LIMIT ?
                    """, (cutoff_time.isoformat(), limit))
                
                rows = await cursor.fetchall()
                
                queries = []
                for row in rows:
                    query_dict = dict(row)
                    query_dict['timestamp'] = datetime.fromisoformat(query_dict['timestamp'])
                    queries.append(LLMQuery(**query_dict))
                
                return queries
                
        except Exception as e:
            self.logger.error(f"Error getting LLM queries: {e}")
            return []

    async def get_llm_stats_by_strategy(self) -> Dict[str, Dict]:
        """Get LLM usage statistics by strategy."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Check if llm_queries table exists
                cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_queries'")
                table_exists = await cursor.fetchone()
                
                if not table_exists:
                    self.logger.info("LLM queries table doesn't exist yet - will be created on first query")
                    return {}
                
                cursor = await db.execute("""
                    SELECT 
                        strategy,
                        COUNT(*) as query_count,
                        SUM(tokens_used) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        AVG(confidence_extracted) as avg_confidence,
                        MIN(timestamp) as first_query,
                        MAX(timestamp) as last_query
                    FROM llm_queries 
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY strategy
                """)
                
                rows = await cursor.fetchall()
                
                stats = {}
                for row in rows:
                    stats[row['strategy']] = {
                        'query_count': row['query_count'],
                        'total_tokens': row['total_tokens'] or 0,
                        'total_cost': row['total_cost'] or 0.0,
                        'avg_confidence': row['avg_confidence'] or 0.0,
                        'first_query': row['first_query'],
                        'last_query': row['last_query']
                    }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting LLM stats: {e}")
            return {}

    async def record_market_analysis(
        self, 
        market_id: str, 
        decision_action: str, 
        confidence: float, 
        cost_usd: float,
        analysis_type: str = 'standard'
    ) -> None:
        """Record that a market was analyzed to prevent duplicate analysis."""
        now = datetime.now().isoformat()
        today = datetime.now().strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(self.db_path) as db:
            # Record the analysis
            await db.execute("""
                INSERT INTO market_analyses (market_id, analysis_timestamp, decision_action, confidence, cost_usd, analysis_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (market_id, now, decision_action, confidence, cost_usd, analysis_type))
            
            # Update daily cost tracking
            await db.execute("""
                INSERT INTO daily_cost_tracking (date, total_ai_cost, analysis_count, decision_count)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_ai_cost = total_ai_cost + excluded.total_ai_cost,
                    analysis_count = analysis_count + 1,
                    decision_count = decision_count + excluded.decision_count
            """, (today, cost_usd, 1 if decision_action != 'SKIP' else 0))
            
            await db.commit()

    async def was_recently_analyzed(self, market_id: str, hours: int = 6) -> bool:
        """Check if market was analyzed within the specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM market_analyses 
                WHERE market_id = ? AND analysis_timestamp > ?
            """, (market_id, cutoff_str))
            count = (await cursor.fetchone())[0]
            return count > 0

    async def get_daily_ai_cost(self, date: str = None) -> float:
        """Get total AI cost for a specific date (defaults to today)."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT total_ai_cost FROM daily_cost_tracking WHERE date = ?
            """, (date,))
            row = await cursor.fetchone()
            return row[0] if row else 0.0

    async def get_market_analysis_count_today(self, market_id: str) -> int:
        """Get number of times market was analyzed today."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM market_analyses 
                WHERE market_id = ? AND DATE(analysis_timestamp) = ?
            """, (market_id, today))
            count = (await cursor.fetchone())[0]
            return count

    async def get_all_trade_logs(self) -> List[TradeLog]:
        """
        Get all trade logs from the database.
        
        Returns:
            A list of TradeLog objects.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM trade_logs")
            rows = await cursor.fetchall()
            
            logs = []
            for row in rows:
                log_dict = dict(row)
                log_dict['entry_timestamp'] = datetime.fromisoformat(log_dict['entry_timestamp'])
                log_dict['exit_timestamp'] = datetime.fromisoformat(log_dict['exit_timestamp'])
                logs.append(TradeLog(**log_dict))
            return logs

    async def update_position_to_live(self, position_id: int, entry_price: float):
        """
        Updates the status and entry price of a position after it has been executed.

        Args:
            position_id: The ID of the position to update.
            entry_price: The actual entry price from the exchange.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE positions 
                SET live = 1, entry_price = ?
                WHERE id = ?
            """, (entry_price, position_id))
            await db.commit()
        self.logger.info(f"Updated position {position_id} to live.")

    async def add_position(self, position: Position) -> Optional[int]:
        """
        Adds a new position to the database, if one doesn't already exist for the same market and side.
        
        Args:
            position: The position to add.
        
        Returns:
            The ID of the newly inserted position, or None if a position already exists.
        """
        existing_position = await self.get_position_by_market_and_side(position.market_id, position.side)
        if existing_position:
            self.logger.warning(f"Position already exists for market {position.market_id} and side {position.side}.")
            return None

        async with aiosqlite.connect(self.db_path) as db:
            position_dict = asdict(position)
            # aiosqlite does not support dataclasses with datetime objects
            position_dict['timestamp'] = position.timestamp.isoformat()

            cursor = await db.execute("""
                INSERT INTO positions (market_id, side, entry_price, quantity, timestamp, rationale, confidence, live, status, strategy, stop_loss_price, take_profit_price, max_hold_hours, target_confidence_change)
                VALUES (:market_id, :side, :entry_price, :quantity, :timestamp, :rationale, :confidence, :live, :status, :strategy, :stop_loss_price, :take_profit_price, :max_hold_hours, :target_confidence_change)
            """, position_dict)
            await db.commit()
            
            # Set has_position to True for the market
            await db.execute("UPDATE markets SET has_position = 1 WHERE market_id = ?", (position.market_id,))
            await db.commit()

            self.logger.info(f"Added position for market {position.market_id}", position_id=cursor.lastrowid)
            return cursor.lastrowid

    async def get_open_positions(self) -> List[Position]:
        """Get all open positions."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM positions WHERE status = 'open'"
            )
            rows = await cursor.fetchall()
            
            positions = []
            for row in rows:
                position_dict = dict(row)
                position_dict['timestamp'] = datetime.fromisoformat(position_dict['timestamp'])
                positions.append(Position(**position_dict))
            
            return positions

    async def close(self) -> None:
        """Close database connections (no-op for aiosqlite)."""
        return None


if __name__ == "__main__":
    import asyncio

    async def _init_db():
        manager = DatabaseManager()
        await manager.initialize()

    asyncio.run(_init_db())