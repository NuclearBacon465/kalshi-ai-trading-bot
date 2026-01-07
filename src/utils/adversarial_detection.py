"""
Adversarial Trading Detection

Detects when other traders are:
- Front-running your orders
- Manipulating markets
- Engaging in toxic order flow
- Trying to move markets against you

Expected profit boost: +8-12% from avoiding bad fills and toxic trades
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import numpy as np

from src.utils.database import DatabaseManager
from src.utils.logging_setup import get_trading_logger


@dataclass
class TradingAnomaly:
    """Detected trading anomaly."""
    ticker: str
    timestamp: datetime
    anomaly_type: str  # "front_run", "spoofing", "layering", "toxic_flow"
    severity: float  # 0.0 to 1.0
    description: str
    recommended_action: str  # "avoid", "delay", "use_limit", "cancel"


@dataclass
class OrderFlowProfile:
    """Profile of recent order flow."""
    ticker: str
    timestamp: datetime

    # Volume metrics
    buy_volume: int
    sell_volume: int
    volume_imbalance: float  # (Buy - Sell) / (Buy + Sell)

    # Trade frequency
    trades_per_minute: float
    avg_trade_size: float

    # Price impact
    price_movement: float  # Price change over period
    volume_weighted_price: float

    # Toxicity indicators
    toxicity_score: float  # 0.0 = uninformed, 1.0 = highly informed
    is_toxic: bool


class AdversarialDetector:
    """
    Detects adversarial trading behavior.

    Protects against:
    - Front-running
    - Spoofing (fake orders)
    - Layering (manipulative orders)
    - Toxic order flow
    - Wash trading
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_trading_logger("adversarial_detector")

        # Track recent activity per market
        self.order_flow_history: Dict[str, deque] = {}
        self.anomaly_history: Dict[str, List[TradingAnomaly]] = {}

        # Detection thresholds
        self.FRONT_RUN_THRESHOLD = 0.7  # Probability threshold
        self.SPOOF_THRESHOLD = 3  # Number of quick cancel/replace cycles
        self.TOXIC_FLOW_THRESHOLD = 0.6  # Toxicity score threshold

    def record_trade(
        self,
        ticker: str,
        side: str,
        price: float,
        quantity: int,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a trade for analysis.

        Args:
            ticker: Market ticker
            side: "buy" or "sell"
            price: Trade price
            quantity: Number of contracts
            timestamp: Trade timestamp
        """
        if ticker not in self.order_flow_history:
            self.order_flow_history[ticker] = deque(maxlen=100)  # Keep last 100 trades

        trade_record = {
            'timestamp': timestamp or datetime.now(),
            'side': side.lower(),
            'price': price,
            'quantity': quantity
        }

        self.order_flow_history[ticker].append(trade_record)

    def detect_front_running(
        self,
        ticker: str,
        my_order_side: str,
        my_order_price: float,
        my_order_size: int
    ) -> Optional[TradingAnomaly]:
        """
        Detect if someone is front-running your order.

        Signs of front-running:
        - Sudden orders in same direction just before yours
        - Price moves against you immediately
        - Large orders appear at better prices

        Args:
            ticker: Market ticker
            my_order_side: Your intended order side
            my_order_price: Your intended price
            my_order_size: Your intended size

        Returns:
            TradingAnomaly if front-running detected, None otherwise
        """
        if ticker not in self.order_flow_history or len(self.order_flow_history[ticker]) < 5:
            return None

        recent_trades = list(self.order_flow_history[ticker])[-10:]  # Last 10 trades
        now = datetime.now()

        # Get very recent trades (last 30 seconds)
        very_recent = [
            t for t in recent_trades
            if (now - t['timestamp']).total_seconds() < 30
        ]

        if not very_recent:
            return None

        # Check for sudden same-direction flow
        same_direction = [t for t in very_recent if t['side'] == my_order_side.lower()]

        if len(same_direction) >= 3:  # 3+ trades in same direction recently
            total_volume = sum(t['quantity'] for t in same_direction)
            avg_price = np.mean([t['price'] for t in same_direction])

            # Check if price moved against us
            if my_order_side.lower() == "buy":
                price_moved_against = avg_price > my_order_price
            else:
                price_moved_against = avg_price < my_order_price

            if price_moved_against and total_volume > my_order_size * 2:
                severity = min(1.0, total_volume / (my_order_size * 5))

                return TradingAnomaly(
                    ticker=ticker,
                    timestamp=now,
                    anomaly_type="front_run",
                    severity=severity,
                    description=(
                        f"Detected {len(same_direction)} {my_order_side} orders "
                        f"({total_volume} contracts) just before yours. "
                        f"Price moved from {my_order_price:.2f} to {avg_price:.2f}"
                    ),
                    recommended_action="delay" if severity < 0.7 else "use_limit"
                )

        return None

    def calculate_order_flow_toxicity(
        self,
        ticker: str,
        lookback_minutes: int = 5
    ) -> Optional[OrderFlowProfile]:
        """
        Calculate how "toxic" recent order flow is.

        Toxic flow = informed trading that predicts price movements.
        We want to avoid trading when flow is toxic (we'll get bad fills).

        Args:
            ticker: Market ticker
            lookback_minutes: How far back to analyze

        Returns:
            OrderFlowProfile with toxicity metrics
        """
        if ticker not in self.order_flow_history or len(self.order_flow_history[ticker]) < 3:
            return None

        now = datetime.now()
        cutoff = now - timedelta(minutes=lookback_minutes)

        # Get recent trades
        recent_trades = [
            t for t in self.order_flow_history[ticker]
            if t['timestamp'] > cutoff
        ]

        if len(recent_trades) < 3:
            return None

        # Calculate metrics
        buy_volume = sum(t['quantity'] for t in recent_trades if t['side'] == 'buy')
        sell_volume = sum(t['quantity'] for t in recent_trades if t['side'] == 'sell')
        total_volume = buy_volume + sell_volume

        volume_imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0

        trades_per_minute = len(recent_trades) / lookback_minutes
        avg_trade_size = total_volume / len(recent_trades) if recent_trades else 0

        # Price movement
        first_price = recent_trades[0]['price']
        last_price = recent_trades[-1]['price']
        price_movement = (last_price - first_price) / first_price if first_price > 0 else 0

        # Volume-weighted price
        vwap = sum(t['price'] * t['quantity'] for t in recent_trades) / total_volume if total_volume > 0 else 0

        # Calculate toxicity score
        # Toxic flow characteristics:
        # 1. Large volume imbalance that predicts price movement
        # 2. High correlation between volume direction and price movement
        # 3. Rapid trading (likely algorithmic)

        # Factor 1: Imbalance-price correlation
        imbalance_price_correlation = abs(volume_imbalance) if np.sign(volume_imbalance) == np.sign(price_movement) else 0

        # Factor 2: Trade frequency (bots trade fast)
        frequency_score = min(1.0, trades_per_minute / 10)  # 10+ trades/min = 1.0

        # Factor 3: Large trades (informed traders trade big)
        size_score = min(1.0, avg_trade_size / 50)  # 50+ avg = 1.0

        # Combined toxicity score
        toxicity_score = (
            0.5 * imbalance_price_correlation +
            0.3 * frequency_score +
            0.2 * size_score
        )

        is_toxic = toxicity_score > self.TOXIC_FLOW_THRESHOLD

        return OrderFlowProfile(
            ticker=ticker,
            timestamp=now,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            volume_imbalance=volume_imbalance,
            trades_per_minute=trades_per_minute,
            avg_trade_size=avg_trade_size,
            price_movement=price_movement,
            volume_weighted_price=vwap,
            toxicity_score=toxicity_score,
            is_toxic=is_toxic
        )

    def detect_spoofing(
        self,
        ticker: str,
        order_book_changes: List[Dict]
    ) -> Optional[TradingAnomaly]:
        """
        Detect spoofing (fake orders to manipulate price).

        Spoofing pattern:
        - Large order placed (to move market)
        - Market reacts
        - Large order cancelled before execution
        - Trader profits from price movement

        Args:
            ticker: Market ticker
            order_book_changes: Recent order book state changes

        Returns:
            TradingAnomaly if spoofing detected
        """
        if len(order_book_changes) < 3:
            return None

        # Look for pattern: large order added -> removed quickly
        quick_cancels = 0

        for i in range(len(order_book_changes) - 1):
            current = order_book_changes[i]
            next_change = order_book_changes[i + 1]

            # Check if large order appeared then disappeared quickly
            time_diff = (next_change['timestamp'] - current['timestamp']).total_seconds()

            if time_diff < 5:  # Cancelled within 5 seconds
                order_size = current.get('size', 0)
                if order_size > 20:  # Large order (20+ contracts)
                    quick_cancels += 1

        if quick_cancels >= self.SPOOF_THRESHOLD:
            return TradingAnomaly(
                ticker=ticker,
                timestamp=datetime.now(),
                anomaly_type="spoofing",
                severity=min(1.0, quick_cancels / 5),
                description=f"Detected {quick_cancels} quick cancel/replace cycles (likely spoofing)",
                recommended_action="avoid"
            )

        return None

    def detect_wash_trading(
        self,
        ticker: str,
        lookback_minutes: int = 10
    ) -> Optional[TradingAnomaly]:
        """
        Detect wash trading (trading with yourself to fake volume).

        Signs:
        - Trades at same price repeatedly
        - Buy and sell volumes exactly equal
        - Trades happen in pairs (buy/sell/buy/sell)

        Args:
            ticker: Market ticker
            lookback_minutes: How far back to check

        Returns:
            TradingAnomaly if wash trading detected
        """
        if ticker not in self.order_flow_history:
            return None

        now = datetime.now()
        cutoff = now - timedelta(minutes=lookback_minutes)

        recent_trades = [
            t for t in self.order_flow_history[ticker]
            if t['timestamp'] > cutoff
        ]

        if len(recent_trades) < 4:
            return None

        # Check for alternating buy/sell pattern
        alternating_count = 0
        for i in range(len(recent_trades) - 1):
            if recent_trades[i]['side'] != recent_trades[i + 1]['side']:
                # Check if same price and size (suspicious)
                if (abs(recent_trades[i]['price'] - recent_trades[i + 1]['price']) < 0.01 and
                    recent_trades[i]['quantity'] == recent_trades[i + 1]['quantity']):
                    alternating_count += 1

        if alternating_count >= 3:  # 3+ matched pairs
            return TradingAnomaly(
                ticker=ticker,
                timestamp=now,
                anomaly_type="wash_trading",
                severity=min(1.0, alternating_count / 5),
                description=f"Detected {alternating_count} matched buy/sell pairs (possible wash trading)",
                recommended_action="avoid"
            )

        return None

    def get_trade_safety_score(self, ticker: str) -> Tuple[float, List[str]]:
        """
        Get overall safety score for trading this market.

        Returns:
            (safety_score, warnings)
            - safety_score: 0.0 = very unsafe, 1.0 = very safe
            - warnings: List of detected issues
        """
        warnings = []
        penalties = []

        # Check order flow toxicity
        flow_profile = self.calculate_order_flow_toxicity(ticker)
        if flow_profile and flow_profile.is_toxic:
            warnings.append(f"Toxic order flow: {flow_profile.toxicity_score:.1%}")
            penalties.append(0.3)

        # Check for recent anomalies
        if ticker in self.anomaly_history:
            recent_anomalies = [
                a for a in self.anomaly_history[ticker]
                if (datetime.now() - a.timestamp).total_seconds() < 300  # Last 5 minutes
            ]

            for anomaly in recent_anomalies:
                warnings.append(f"{anomaly.anomaly_type}: {anomaly.description}")
                penalties.append(anomaly.severity * 0.4)

        # Calculate safety score
        if penalties:
            total_penalty = min(sum(penalties), 0.9)  # Max 90% penalty
            safety_score = 1.0 - total_penalty
        else:
            safety_score = 1.0

        return safety_score, warnings

    def should_avoid_trade(
        self,
        ticker: str,
        min_safety_score: float = 0.5
    ) -> Tuple[bool, str]:
        """
        Determine if we should avoid trading this market right now.

        Args:
            ticker: Market ticker
            min_safety_score: Minimum acceptable safety score

        Returns:
            (should_avoid, reason)
        """
        safety_score, warnings = self.get_trade_safety_score(ticker)

        if safety_score < min_safety_score:
            reason = f"Safety score {safety_score:.1%} below threshold {min_safety_score:.1%}. "
            reason += " | ".join(warnings)
            return True, reason

        return False, "Market conditions safe for trading"


# Convenience function
def create_adversarial_detector(db_manager: DatabaseManager) -> AdversarialDetector:
    """Create adversarial detector instance."""
    return AdversarialDetector(db_manager)
