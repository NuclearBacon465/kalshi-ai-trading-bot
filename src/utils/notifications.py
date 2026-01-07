"""
Trade Notification System

Real-time notifications for trading activity with sound alerts and detailed logging.
"""

import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any


class TradeNotifier:
    """
    Notification system for trade events.

    Features:
    - Terminal beep for trade events
    - Colored console output
    - File logging with timestamps
    - Desktop notifications (if available)
    """

    def __init__(self, enable_sound: bool = True, enable_desktop: bool = False):
        self.enable_sound = enable_sound
        self.enable_desktop = enable_desktop

        # Colors for terminal output
        self.COLORS = {
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'BLUE': '\033[94m',
            'MAGENTA': '\033[95m',
            'CYAN': '\033[96m',
            'WHITE': '\033[97m',
            'BOLD': '\033[1m',
            'END': '\033[0m'
        }

    def beep(self, count: int = 1):
        """Play terminal beep sound."""
        if self.enable_sound:
            for _ in range(count):
                print('\a', end='', flush=True)

    def notify_trade_opened(self, market_id: str, side: str, quantity: int,
                           price: float, confidence: float, edge: float):
        """Notify when a trade is opened."""
        self.beep(2)  # Double beep

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""
{self.COLORS['BOLD']}{self.COLORS['GREEN']}
╔══════════════════════════════════════════════════════════════╗
║           🚀 NEW TRADE OPENED 🚀                              ║
╚══════════════════════════════════════════════════════════════╝
{self.COLORS['END']}
{self.COLORS['CYAN']}Time:{self.COLORS['END']} {timestamp}
{self.COLORS['CYAN']}Market:{self.COLORS['END']} {market_id}
{self.COLORS['CYAN']}Side:{self.COLORS['END']} {self.COLORS['BOLD']}{side.upper()}{self.COLORS['END']}
{self.COLORS['CYAN']}Quantity:{self.COLORS['END']} {quantity} contracts @ ${price:.2f}
{self.COLORS['CYAN']}Total Value:{self.COLORS['END']} ${quantity * price:.2f}
{self.COLORS['CYAN']}Confidence:{self.COLORS['END']} {confidence:.1%}
{self.COLORS['CYAN']}Edge:{self.COLORS['END']} {self.COLORS['GREEN']}{edge:.2%}{self.COLORS['END']}
{self.COLORS['BOLD']}{self.COLORS['GREEN']}
════════════════════════════════════════════════════════════════
{self.COLORS['END']}
"""
        print(message, flush=True)

        # Also log to file
        self._log_to_file('TRADE_OPENED', {
            'market_id': market_id,
            'side': side,
            'quantity': quantity,
            'price': price,
            'confidence': confidence,
            'edge': edge
        })

    def notify_trade_closed(self, market_id: str, side: str, quantity: int,
                           entry_price: float, exit_price: float, profit: float,
                           profit_pct: float):
        """Notify when a trade is closed."""
        is_profit = profit > 0
        self.beep(3 if is_profit else 1)  # Triple beep for profit, single for loss

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        color = self.COLORS['GREEN'] if is_profit else self.COLORS['RED']
        emoji = '💰' if is_profit else '📉'

        message = f"""
{self.COLORS['BOLD']}{color}
╔══════════════════════════════════════════════════════════════╗
║           {emoji} TRADE CLOSED {emoji}                              ║
╚══════════════════════════════════════════════════════════════╝
{self.COLORS['END']}
{self.COLORS['CYAN']}Time:{self.COLORS['END']} {timestamp}
{self.COLORS['CYAN']}Market:{self.COLORS['END']} {market_id}
{self.COLORS['CYAN']}Side:{self.COLORS['END']} {self.COLORS['BOLD']}{side.upper()}{self.COLORS['END']}
{self.COLORS['CYAN']}Quantity:{self.COLORS['END']} {quantity} contracts
{self.COLORS['CYAN']}Entry Price:{self.COLORS['END']} ${entry_price:.2f}
{self.COLORS['CYAN']}Exit Price:{self.COLORS['END']} ${exit_price:.2f}
{self.COLORS['CYAN']}Profit/Loss:{self.COLORS['END']} {color}${profit:+.2f} ({profit_pct:+.2%}){self.COLORS['END']}
{self.COLORS['BOLD']}{color}
════════════════════════════════════════════════════════════════
{self.COLORS['END']}
"""
        print(message, flush=True)

        # Also log to file
        self._log_to_file('TRADE_CLOSED', {
            'market_id': market_id,
            'side': side,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit': profit,
            'profit_pct': profit_pct
        })

    def notify_order_placed(self, order_id: str, market_id: str, action: str,
                           side: str, quantity: int, order_type: str):
        """Notify when an order is placed."""
        self.beep(1)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""
{self.COLORS['BLUE']}📝 ORDER PLACED{self.COLORS['END']} - {timestamp}
   Order ID: {order_id[:20]}...
   Market: {market_id}
   Action: {self.COLORS['BOLD']}{action.upper()}{self.COLORS['END']} {side.upper()} ({order_type})
   Quantity: {quantity} contracts
{self.COLORS['BLUE']}────────────────────────────────────────────────────────────────{self.COLORS['END']}
"""
        print(message, flush=True)

        self._log_to_file('ORDER_PLACED', {
            'order_id': order_id,
            'market_id': market_id,
            'action': action,
            'side': side,
            'quantity': quantity,
            'order_type': order_type
        })

    def notify_order_filled(self, order_id: str, market_id: str, fill_price: float):
        """Notify when an order is filled."""
        self.beep(2)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""
{self.COLORS['GREEN']}✅ ORDER FILLED{self.COLORS['END']} - {timestamp}
   Order ID: {order_id[:20]}...
   Market: {market_id}
   Fill Price: ${fill_price:.2f}
{self.COLORS['GREEN']}────────────────────────────────────────────────────────────────{self.COLORS['END']}
"""
        print(message, flush=True)

        self._log_to_file('ORDER_FILLED', {
            'order_id': order_id,
            'market_id': market_id,
            'fill_price': fill_price
        })

    def notify_opportunity_found(self, market_id: str, edge: float, confidence: float):
        """Notify when a trading opportunity is found."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""
{self.COLORS['YELLOW']}🎯 OPPORTUNITY FOUND{self.COLORS['END']} - {timestamp}
   Market: {market_id}
   Edge: {self.COLORS['GREEN']}{edge:.2%}{self.COLORS['END']}
   Confidence: {confidence:.1%}
{self.COLORS['YELLOW']}────────────────────────────────────────────────────────────────{self.COLORS['END']}
"""
        print(message, flush=True)

        self._log_to_file('OPPORTUNITY_FOUND', {
            'market_id': market_id,
            'edge': edge,
            'confidence': confidence
        })

    def notify_daily_summary(self, total_trades: int, wins: int, losses: int,
                            total_profit: float, win_rate: float):
        """Notify daily summary."""
        self.beep(3)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        color = self.COLORS['GREEN'] if total_profit > 0 else self.COLORS['RED']

        message = f"""
{self.COLORS['BOLD']}{self.COLORS['MAGENTA']}
╔══════════════════════════════════════════════════════════════╗
║           📊 DAILY TRADING SUMMARY 📊                         ║
╚══════════════════════════════════════════════════════════════╝
{self.COLORS['END']}
{self.COLORS['CYAN']}Date:{self.COLORS['END']} {timestamp}
{self.COLORS['CYAN']}Total Trades:{self.COLORS['END']} {total_trades}
{self.COLORS['CYAN']}Wins:{self.COLORS['END']} {self.COLORS['GREEN']}{wins}{self.COLORS['END']} | {self.COLORS['CYAN']}Losses:{self.COLORS['END']} {self.COLORS['RED']}{losses}{self.COLORS['END']}
{self.COLORS['CYAN']}Win Rate:{self.COLORS['END']} {win_rate:.1%}
{self.COLORS['CYAN']}Total P/L:{self.COLORS['END']} {color}${total_profit:+.2f}{self.COLORS['END']}
{self.COLORS['BOLD']}{self.COLORS['MAGENTA']}
════════════════════════════════════════════════════════════════
{self.COLORS['END']}
"""
        print(message, flush=True)

        self._log_to_file('DAILY_SUMMARY', {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'total_profit': total_profit,
            'win_rate': win_rate
        })

    def _log_to_file(self, event_type: str, data: Dict[str, Any]):
        """Log event to file."""
        timestamp = datetime.now().isoformat()

        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'trade_notifications.log')

        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {event_type}: {data}\n")


# Global notifier instance
_notifier = None

def get_notifier() -> TradeNotifier:
    """Get or create global notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TradeNotifier(enable_sound=True, enable_desktop=False)
    return _notifier
