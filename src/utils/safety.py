"""
Safety utilities for trading execution.
"""

from typing import Optional

from src.config.settings import settings
from src.utils.logging_setup import get_trading_logger


def is_kill_switch_enabled() -> bool:
    """Return True if the global kill switch is enabled."""
    return bool(getattr(settings.trading, "kill_switch_enabled", False))


def enforce_kill_switch(live_mode: bool, logger: Optional[object] = None) -> bool:
    """
    Enforce the kill switch by downgrading live_mode when enabled.

    Returns the effective live_mode to use.
    """
    if not live_mode:
        return False

    if is_kill_switch_enabled():
        active_logger = logger or get_trading_logger("safety")
        active_logger.warning("🛑 Kill switch enabled; forcing live trading OFF.")
        return False

    return live_mode


def should_halt_trading(logger: Optional[object] = None) -> bool:
    """
    Return True if trading should be halted due to the kill switch.
    """
    if not is_kill_switch_enabled():
        return False

    active_logger = logger or get_trading_logger("safety")
    active_logger.warning("🛑 Kill switch enabled; skipping trading execution.")
    return True
