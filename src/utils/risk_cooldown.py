"""Utilities for persisting risk cooldown state."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RiskCooldownState:
    cooldown_until: datetime
    violations: List[str]


def _state_path(db_path: str) -> Path:
    db_file = Path(db_path)
    if db_file.suffix:
        return db_file.with_suffix(f"{db_file.suffix}.risk_cooldown.json")
    return db_file.with_name(f"{db_file.name}.risk_cooldown.json")


def save_risk_cooldown_state(
    db_path: str,
    cooldown_until: datetime,
    violations: List[str],
) -> Path:
    state = {
        "cooldown_until": cooldown_until.isoformat(),
        "violations": violations,
        "updated_at": datetime.now().isoformat(),
    }
    path = _state_path(db_path)
    try:
        path.write_text(json.dumps(state, indent=2))
    except Exception as exc:
        logger.error("Failed to write risk cooldown state: %s", exc)
    return path


def load_risk_cooldown_state(db_path: str) -> Optional[RiskCooldownState]:
    path = _state_path(db_path)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
        cooldown_until = datetime.fromisoformat(raw["cooldown_until"])
        violations = list(raw.get("violations", []))
        return RiskCooldownState(cooldown_until=cooldown_until, violations=violations)
    except Exception as exc:
        logger.error("Failed to read risk cooldown state: %s", exc)
        return None


def clear_risk_cooldown_state(db_path: str) -> None:
    path = _state_path(db_path)
    if path.exists():
        try:
            path.unlink()
        except Exception as exc:
            logger.error("Failed to clear risk cooldown state: %s", exc)


def is_risk_cooldown_active(
    db_path: str, now: Optional[datetime] = None
) -> Tuple[bool, Optional[RiskCooldownState]]:
    state = load_risk_cooldown_state(db_path)
    if not state:
        return False, None
    now = now or datetime.now()
    if now < state.cooldown_until:
        return True, state
    clear_risk_cooldown_state(db_path)
    return False, None
