"""
Health monitoring utilities for persistent safe-mode state.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


HEALTH_STATE_PATH = Path("logs/health_state.json")
FAILURE_THRESHOLDS = {
    "kalshi": 5,
    "xai": 5,
}


def _default_state() -> Dict[str, object]:
    return {
        "safe_mode": False,
        "safe_mode_reason": None,
        "safe_mode_triggered_at": None,
        "failures": {"kalshi": 0, "xai": 0},
        "last_updated": datetime.utcnow().isoformat(),
    }


def _ensure_logs_dir() -> None:
    HEALTH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_health_state() -> Dict[str, object]:
    _ensure_logs_dir()
    if HEALTH_STATE_PATH.exists():
        try:
            with HEALTH_STATE_PATH.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
        except json.JSONDecodeError:
            state = _default_state()
    else:
        state = _default_state()

    state.setdefault("failures", {"kalshi": 0, "xai": 0})
    state.setdefault("safe_mode", False)
    state.setdefault("safe_mode_reason", None)
    state.setdefault("safe_mode_triggered_at", None)
    state["last_updated"] = datetime.utcnow().isoformat()
    return state


def save_health_state(state: Dict[str, object]) -> None:
    _ensure_logs_dir()
    state["last_updated"] = datetime.utcnow().isoformat()
    with HEALTH_STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def record_failure(service: str) -> Dict[str, object]:
    if service not in FAILURE_THRESHOLDS:
        raise ValueError(f"Unknown service name for health tracking: {service}")

    state = load_health_state()
    failures = state.setdefault("failures", {"kalshi": 0, "xai": 0})
    failures[service] = failures.get(service, 0) + 1

    if failures[service] >= FAILURE_THRESHOLDS[service]:
        state["safe_mode"] = True
        state["safe_mode_reason"] = f"{service}_failure_threshold_exceeded"
        state["safe_mode_triggered_at"] = datetime.utcnow().isoformat()

    save_health_state(state)
    return state


def is_safe_mode_active() -> bool:
    state = load_health_state()
    return bool(state.get("safe_mode", False))


def set_safe_mode(active: bool, reason: Optional[str] = None) -> Dict[str, object]:
    state = load_health_state()
    state["safe_mode"] = active
    state["safe_mode_reason"] = reason if active else None
    state["safe_mode_triggered_at"] = datetime.utcnow().isoformat() if active else None
    save_health_state(state)
    return state
