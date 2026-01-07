"""Safety utilities for trading controls."""

from src.config.settings import settings


def is_kill_switch_enabled() -> bool:
    """Return True when the trading kill switch is enabled."""
    return bool(getattr(settings.trading, "kill_switch_enabled", False))
