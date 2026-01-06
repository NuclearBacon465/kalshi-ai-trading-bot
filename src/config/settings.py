"""
Configuration settings for the Kalshi trading system.
Manages trading parameters, API configurations, and risk management settings.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class APIConfig:
    """API configuration settings."""
    kalshi_api_key: str = field(default_factory=lambda: os.getenv("KALSHI_API_KEY", ""))
    kalshi_base_url: str = "https://api.elections.kalshi.com"  # Updated to new API endpoint
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    xai_api_key: str = field(default_factory=lambda: os.getenv("XAI_API_KEY", ""))
    openai_base_url: str = "https://api.openai.com/v1"


# Trading strategy configuration - INCREASED AGGRESSIVENESS
@dataclass
class TradingConfig:
    """Trading strategy configuration."""
    # Position sizing and risk management - MADE MORE AGGRESSIVE  
    max_position_size_pct: float = 50.0  # INCREASED: Back to 5% per position (was 3%)
    max_portfolio_exposure_pct: float = 90.0  # allow up to 90% deployed across open positions
    max_daily_loss_pct: float = 50.0    # INCREASED: Allow 15% daily loss (was 10%) 
    max_positions: int = 30              # INCREASED: Allow 15 concurrent positions (was 10)
    min_balance: float = 0.0           # REDUCED: Lower minimum to trade more (was 100)
    
    # Market filtering criteria - MUCH MORE PERMISSIVE
    min_volume: float = 50.0            # DECREASED: Much lower volume requirement (was 500, now 200)
    max_time_to_expiry_days: int = 30    # INCREASED: Allow longer timeframes (was 14, now 30)
    
    # AI decision making - HIGH RISK HIGH REWARD
    min_confidence_to_trade: float = 0.50   # AGGRESSIVE: Take more trades with 50%+ confidence for higher volume
    scan_interval_seconds: int = 10      # DECREASED: Scan more frequently (was 60, now 30)
    
    # AI model configuration
    primary_model: str = "grok-4" # DO NOT CHANGE THIS UNDER ANY CIRCUMSTANCES
    fallback_model: str = "grok-3"  # Fallback to available model
    ai_temperature: float = 0  # Lower temperature for more consistent JSON output
    ai_max_tokens: int = 8000    # Reasonable limit for reasoning models (grok-4 works better with 8000)
    
    # Position sizing (LEGACY - now using Kelly-primary approach)
    default_position_size: float = 3.0  # REDUCED: Now using Kelly Criterion as primary method (was 5%, now 3%)
    position_size_multiplier: float = 1.0  # Multiplier for AI confidence
    
    # Kelly Criterion settings (PRIMARY position sizing method) - AGGRESSIVE FOR HIGH RISK/REWARD
    use_kelly_criterion: bool = True        # Use Kelly Criterion for position sizing (PRIMARY METHOD)
    kelly_fraction: float = 0.75            # AGGRESSIVE: 75% Kelly for higher returns (high risk/reward)
    max_single_position: float = 0.40       # AGGRESSIVE: 40% max position size for bigger bets
    
    # Trading frequency - MORE FREQUENT
    market_scan_interval: int = 15          # DECREASED: Scan every 30 seconds (was 60)
    position_check_interval: int = 10       # DECREASED: Check positions every 15 seconds (was 30)
    max_trades_per_hour: int = 60           # INCREASED: Allow more trades per hour (was 10, now 20)
    run_interval_minutes: int = 5          # DECREASED: Run more frequently (was 15, now 10)
    num_processor_workers: int = 8      # Number of concurrent market processor workers
    
    # Market selection preferences
    preferred_categories: List[str] = field(default_factory=lambda: [])
    excluded_categories: List[str] = field(default_factory=lambda: [])
    
    # High-confidence, near-expiry strategy
    enable_high_confidence_strategy: bool = True
    high_confidence_threshold: float = 0.95  # LLM confidence needed
    high_confidence_market_odds: float = 0.90 # Market price to look for
    high_confidence_expiry_hours: int = 24   # Max hours until expiry

    # AI trading criteria - AGGRESSIVE FOR HIGH VOLUME
    max_analysis_cost_per_decision: float = 0.15  # INCREASED: Allow higher cost per decision (was 0.10, now 0.15)
    min_confidence_threshold: float = 0.50  # AGGRESSIVE: Take more trades at 50%+ confidence

    # Cost control and market analysis frequency - MORE PERMISSIVE
    daily_ai_budget: float = 100.0  # ⚡ OPTIMIZED: 5x increase for maximum opportunity detection (was 20.0, now 100.0)
    max_ai_cost_per_decision: float = 0.20  # INCREASED: Higher per-decision cost (was 0.15, now 0.20)
    analysis_cooldown_hours: int = 1  # DECREASED: Shorter cooldown (was 6, now 3)
    max_analyses_per_market_per_day: int = 10  # INCREASED: More analyses per day (was 2, now 4)
    
    # Daily AI spending limits - SAFETY CONTROLS
    daily_ai_cost_limit: float = 150.0  # ⚡ OPTIMIZED: Higher limit to match budget (was 50.0, now 150.0)
    enable_daily_cost_limiting: bool = True  # Enable daily cost limits
    sleep_when_limit_reached: bool = True  # Sleep until next day when limit reached

    # Enhanced market filtering to reduce analyses - MORE PERMISSIVE
    min_volume_for_ai_analysis: float = 25.0  # DECREASED: Much lower threshold (was 50, now 25 for more opportunities)
    exclude_low_liquidity_categories: List[str] = field(default_factory=lambda: [
        # REMOVED weather and entertainment - trade all categories
    ])

    # === EXECUTION MODES (strategies read these) ===
    live_trading_enabled: bool = True      # MUST be True to actually send orders
    paper_trading_mode: bool = False      # True = simulate only
    
    # === PORTFOLIO / STRATEGY SETTINGS (code references settings.trading.*) ===
    total_capital: Optional[float] = None  # None = use live Kalshi balance
    use_risk_parity: bool = True

    min_position_size: float = 2.0         # allow tiny test trades
    max_position_size: float = 1000.0      # high cap; % caps usually bind first

    max_concurrent_markets: int = 50
    ev_threshold: float = 0.01             # lower = more trades

    skip_news_for_low_volume: bool = True
    news_search_volume_threshold: float = 200.0

    target_sharpe: float = 0.10


@dataclass
class LoggingConfig:
    """Logging configuration."""
    log_level: str = "DEBUG"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/trading_system.log"
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    max_log_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


# BEAST MODE UNIFIED TRADING SYSTEM CONFIGURATION 🚀
# These settings control the advanced multi-strategy trading system

# === CAPITAL ALLOCATION ACROSS STRATEGIES ===
# Allocate capital across different trading approaches
market_making_allocation: float = 0.40  # 40% for market making (spread profits)
directional_allocation: float = 0.50    # 50% for directional trading (AI predictions) 
arbitrage_allocation: float = 0.10      # 10% for arbitrage opportunities

# === PORTFOLIO OPTIMIZATION SETTINGS ===
# Kelly Criterion is now the PRIMARY position sizing method (moved to TradingConfig)
# total_capital: DYNAMICALLY FETCHED from Kalshi balance - never hardcoded!
use_risk_parity: bool = True            # Equal risk allocation vs equal capital
rebalance_hours: int = 6                # Rebalance portfolio every 6 hours
min_position_size: float = 5.0          # Minimum position size ($5 vs $10)
max_opportunities_per_batch: int = 50   # Limit opportunities to prevent optimization issues

# === RISK MANAGEMENT LIMITS ===
# Portfolio-level risk constraints (EXTREMELY RELAXED FOR TESTING)
max_volatility: float = 0.80            # Very high volatility allowed (80%)
max_correlation: float = 0.95           # Very high correlation allowed (95%)
max_drawdown: float = 0.50              # High drawdown tolerance (50%)
max_sector_exposure: float = 0.90       # Very high sector concentration (90%)

# === PERFORMANCE TARGETS ===
# System performance objectives - MORE AGGRESSIVE FOR MORE TRADES
target_sharpe: float = 0.3              # DECREASED: Lower Sharpe requirement (was 0.5, now 0.3)
target_return: float = 0.15             # INCREASED: Higher return target (was 0.10, now 0.15)
min_trade_edge: float = 0.05           # DECREASED: Lower edge requirement (was 0.08, now 5% for more trades)
min_confidence_for_large_size: float = 0.40  # DECREASED: Lower confidence requirement (was 0.50, now 40%)

# === DYNAMIC EXIT STRATEGIES ===
# Enhanced exit strategy settings - MORE AGGRESSIVE
use_dynamic_exits: bool = True
profit_threshold: float = 0.20          # DECREASED: Take profits sooner (was 0.25, now 0.20)
loss_threshold: float = 0.15            # INCREASED: Allow larger losses (was 0.10, now 0.15)
confidence_decay_threshold: float = 0.25  # INCREASED: Allow more confidence decay (was 0.20, now 0.25)
max_hold_time_hours: int = 240          # INCREASED: Hold longer (was 168, now 240 hours = 10 days)
volatility_adjustment: bool = True      # Adjust exits based on volatility

# === MARKET MAKING STRATEGY ===
# Settings for limit order market making - MORE AGGRESSIVE
enable_market_making: bool = True       # Enable market making strategy
min_spread_for_making: float = 0.005    # DECREASED: Accept smaller spreads (was 0.01, now 0.5¢ for more opportunities)
max_inventory_risk: float = 0.15        # INCREASED: Allow higher inventory risk (was 0.10, now 15%)
order_refresh_minutes: int = 15         # Refresh orders every 15 minutes
max_orders_per_market: int = 4          # Maximum orders per market (2 each side)

# === MARKET SELECTION (ENHANCED FOR MORE OPPORTUNITIES) ===
# Removed time restrictions - trade ANY deadline with dynamic exits!
# max_time_to_expiry_days: REMOVED      # No longer used - trade any timeline!
min_volume_for_analysis: float = 100.0  # DECREASED: Much lower minimum volume (was 200, now 100 for more opportunities)
min_volume_for_market_making: float = 250.0  # DECREASED: Lower volume for market making (was 500, now 250)
min_price_movement: float = 0.02        # DECREASED: Lower minimum range (was 0.05, now 2¢)
max_bid_ask_spread: float = 0.15        # INCREASED: Allow wider spreads (was 0.10, now 15¢)
min_confidence_long_term: float = 0.45  # DECREASED: Lower confidence for distant expiries (was 0.65, now 45%)

# === COST OPTIMIZATION (MORE GENEROUS) ===
# Enhanced cost controls for the beast mode system
daily_ai_budget: float = 100.0          # ⚡ OPTIMIZED: 5x increase for maximum opportunity detection (was 15.0, now 100.0)
max_ai_cost_per_decision: float = 0.20  # INCREASED: Higher per-decision limit (was 0.12, now 0.20)
analysis_cooldown_hours: int = 1        # ⚡ OPTIMIZED: Shorter cooldown for more frequent re-analysis (was 2, now 1)
max_analyses_per_market_per_day: int = 6  # INCREASED: More analyses per day (was 3, now 6)
skip_news_for_low_volume: bool = True   # Skip expensive searches for low volume
news_search_volume_threshold: float = 1000.0  # News threshold

# === SYSTEM BEHAVIOR ===
# Overall system behavior settings
beast_mode_enabled: bool = True         # Enable the unified advanced system
fallback_to_legacy: bool = True         # Fallback to legacy system if needed
live_trading_enabled: bool = True       # Set to True for live trading
paper_trading_mode: bool = False        # Paper trading for testing
log_level: str = "INFO"                 # Logging level
performance_monitoring: bool = True     # Enable performance monitoring

# === ADVANCED FEATURES ===
# Cutting-edge features for maximum performance
cross_market_arbitrage: bool = False    # Enable when arbitrage module ready
multi_model_ensemble: bool = False      # Use multiple AI models (future)
sentiment_analysis: bool = False        # News sentiment analysis (future)
options_strategies: bool = False        # Complex options strategies (future)
algorithmic_execution: bool = False     # Smart order execution (future)


@dataclass
class Settings:
    """Main settings class combining all configuration."""
    api: APIConfig = field(default_factory=APIConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.api.kalshi_api_key:
            raise ValueError("KALSHI_API_KEY environment variable is required")
        
        if not self.api.xai_api_key:
            raise ValueError("XAI_API_KEY environment variable is required")
        
        if self.trading.max_position_size_pct <= 0 or self.trading.max_position_size_pct > 100:
            raise ValueError("max_position_size_pct must be between 0 and 100")
        
        if self.trading.min_confidence_to_trade <= 0 or self.trading.min_confidence_to_trade > 1:
            raise ValueError("min_confidence_to_trade must be between 0 and 1")
        
        return True


# Global settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate()
except ValueError as e:
    print(f"Configuration validation error: {e}")
    print("Please check your environment variables and configuration.")
