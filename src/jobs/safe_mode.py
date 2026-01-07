"""
Safe mode utility CLI.

Allows manual inspection and reset of the trading safe mode state.
"""

import argparse
import json

from src.utils.database import DatabaseManager


def _print_state(state: dict) -> None:
    print(json.dumps(state, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading safe mode utility")
    parser.add_argument(
        "--state-path",
        default="trading_state.json",
        help="Path to the trading state file"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show current safe mode status")
    subparsers.add_parser("reset", help="Reset safe mode and failure counter")

    args = parser.parse_args()

    db_manager = DatabaseManager(state_path=args.state_path)

    if args.command == "status":
        _print_state(db_manager.get_safe_mode_state())
        return

    if args.command == "reset":
        db_manager.reset_safe_mode()
        _print_state(db_manager.get_safe_mode_state())
        return


if __name__ == "__main__":
    main()
