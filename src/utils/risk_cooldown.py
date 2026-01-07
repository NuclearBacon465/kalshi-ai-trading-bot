"""
Utility helpers for persisting and checking risk cooldown state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class RiskCooldownStatus:
    active: bool
    cooldown_until: Optional[datetime]
    remaining_seconds: float
    reason: Optional[str] = None


def _cooldown_path(db_path: str) -> Path:
    db_file = Path(db_path)
    return db_file.with_name(f"{db_file.stem}.risk_cooldown.json")


def set_risk_cooldown(db_path: str, duration: timedelta, reason: str) -> datetime:
    cooldown_until = datetime.now() + duration
    payload = {
        "cooldown_until": cooldown_until.isoformat(),
        "reason": reason,
        "duration_seconds": int(duration.total_seconds()),
        "updated_at": datetime.now().isoformat(),
    }
    path = _cooldown_path(db_path)
    path.write_text(json.dumps(payload, indent=2))
    return cooldown_until


def get_risk_cooldown_status(db_path: str) -> RiskCooldownStatus:
    path = _cooldown_path(db_path)
    if not path.exists():
        return RiskCooldownStatus(active=False, cooldown_until=None, remaining_seconds=0.0)

    try:
        payload = json.loads(path.read_text())
        cooldown_until_raw = payload.get("cooldown_until")
        reason = payload.get("reason")
        if not cooldown_until_raw:
            return RiskCooldownStatus(active=False, cooldown_until=None, remaining_seconds=0.0)
        cooldown_until = datetime.fromisoformat(cooldown_until_raw)
    except Exception:
        return RiskCooldownStatus(active=False, cooldown_until=None, remaining_seconds=0.0)

    now = datetime.now()
    remaining = (cooldown_until - now).total_seconds()
    if remaining <= 0:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        return RiskCooldownStatus(active=False, cooldown_until=None, remaining_seconds=0.0)

    return RiskCooldownStatus(
        active=True,
        cooldown_until=cooldown_until,
        remaining_seconds=remaining,
        reason=reason,
    )
