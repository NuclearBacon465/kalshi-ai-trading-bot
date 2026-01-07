#!/usr/bin/env python3
"""
🔍 Kalshi Trading Bot Monitor

Real-time monitoring script to verify your bot is placing trades and working correctly.

Usage:
    python3 monitor_trades.py --check-balance    # Check your current balance
    python3 monitor_trades.py --check-positions  # Check current positions
    python3 monitor_trades.py --check-trades     # Check recent trades
    python3 monitor_trades.py --watch            # Watch for new trades in real-time
    python3 monitor_trades.py --verify           # Full verification check
    python3 monitor_trades.py --dashboard        # Launch monitoring dashboard
"""

import asyncio
import argparse
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

from src.clients.kalshi_client import KalshiClient
from src.config.settings import settings


class TradeMonitor:
    """Monitor trading activity and verify bot is working"""

    def __init__(self):
        self.kalshi_client = None
        self.last_order_count = 0
        self.last_position_count = 0
        self.start_balance = 0

    async def initialize(self):
        """Initialize the Kalshi client"""
        self.kalshi_client = KalshiClient()
        print("✅ Connected to Kalshi API")

    async def close(self):
        """Close connections"""
        if self.kalshi_client:
            await self.kalshi_client.close()

    async def check_balance(self):
        """Check current account balance"""
        print("\n" + "="*70)
        print("💰 ACCOUNT BALANCE")
        print("="*70)

        try:
            balance_response = await self.kalshi_client.get_balance()
            balance_cents = balance_response.get('balance', 0)
            balance_dollars = balance_cents / 100

            print(f"  Current Balance: ${balance_dollars:.2f}")
            print(f"  Balance (cents): {balance_cents}¢")

            self.start_balance = balance_dollars

            return balance_dollars

        except Exception as e:
            print(f"  ❌ Error checking balance: {e}")
            return None

    async def check_positions(self, verbose=True):
        """Check current open positions"""
        if verbose:
            print("\n" + "="*70)
            print("📊 CURRENT POSITIONS")
            print("="*70)

        try:
            positions_response = await self.kalshi_client.get_positions()
            positions = positions_response.get('positions', [])

            if not positions:
                if verbose:
                    print("  No open positions")
                return []

            if verbose:
                print(f"  Total Positions: {len(positions)}")
                print()

            total_value = 0
            for i, pos in enumerate(positions, 1):
                market_id = pos.get('market_id', 'Unknown')
                ticker = pos.get('ticker', 'Unknown')
                side = pos.get('side', 'unknown')
                quantity = pos.get('quantity', 0)
                # Get current market price
                try:
                    market_data = await self.kalshi_client.get_market(market_id)
                    market_info = market_data.get('market', {})
                    if side == 'yes':
                        current_price = market_info.get('yes_price', 50) / 100
                    else:
                        current_price = market_info.get('no_price', 50) / 100
                    position_value = quantity * current_price
                    total_value += position_value
                except:
                    position_value = quantity * 0.50  # Estimate

                if verbose:
                    print(f"  [{i}] {ticker}")
                    print(f"      Side: {side.upper()}")
                    print(f"      Quantity: {quantity} contracts")
                    print(f"      Value: ${position_value:.2f}")
                    print()

            if verbose:
                print(f"  Total Position Value: ${total_value:.2f}")

            self.last_position_count = len(positions)
            return positions

        except Exception as e:
            if verbose:
                print(f"  ❌ Error checking positions: {e}")
            return []

    async def check_orders(self, limit=20, verbose=True):
        """Check recent orders"""
        if verbose:
            print("\n" + "="*70)
            print("📝 RECENT ORDERS")
            print("="*70)

        try:
            orders_response = await self.kalshi_client.get_orders()
            orders = orders_response.get('orders', [])

            if not orders:
                if verbose:
                    print("  No orders found")
                return []

            # Show most recent orders
            recent_orders = orders[:limit]

            if verbose:
                print(f"  Total Orders: {len(orders)}")
                print(f"  Showing: Most recent {min(limit, len(orders))}")
                print()

            for i, order in enumerate(recent_orders, 1):
                order_id = order.get('order_id', 'Unknown')
                ticker = order.get('ticker', 'Unknown')
                action = order.get('action', 'unknown')
                side = order.get('side', 'unknown')
                order_type = order.get('type', 'unknown')
                count = order.get('count', 0)
                status = order.get('status', 'unknown')
                created_time = order.get('created_time', '')

                # Parse timestamp
                try:
                    if created_time:
                        dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = 'Unknown'
                except:
                    time_str = created_time

                if verbose:
                    status_emoji = "✅" if status == "filled" else "⏳" if status == "pending" else "❌"
                    print(f"  [{i}] {status_emoji} {time_str}")
                    print(f"      Order ID: {order_id[:20]}...")
                    print(f"      Market: {ticker}")
                    print(f"      Action: {action.upper()} {side.upper()} ({order_type})")
                    print(f"      Quantity: {count} contracts")
                    print(f"      Status: {status.upper()}")
                    print()

            self.last_order_count = len(orders)
            return orders

        except Exception as e:
            if verbose:
                print(f"  ❌ Error checking orders: {e}")
            return []

    async def check_fills(self, limit=10):
        """Check recent filled orders"""
        print("\n" + "="*70)
        print("✅ RECENT FILLED ORDERS")
        print("="*70)

        try:
            fills_response = await self.kalshi_client.get_fills(limit=limit)
            fills = fills_response.get('fills', [])

            if not fills:
                print("  No filled orders yet")
                print()
                print("  ⚠️  This means the bot hasn't placed any successful trades")
                print("     Check that:")
                print("       - The bot is running (python3 beast_mode_bot.py --live)")
                print("       - Markets are open and have liquidity")
                print("       - Bot found opportunities with sufficient edge")
                return []

            print(f"  Total Fills: {len(fills)}")
            print()

            total_spent = 0
            for i, fill in enumerate(fills, 1):
                ticker = fill.get('ticker', 'Unknown')
                action = fill.get('action', 'unknown')
                side = fill.get('side', 'unknown')
                count = fill.get('count', 0)
                price = fill.get('price', 0) / 100  # Convert cents to dollars
                total_cost = count * price
                total_spent += total_cost if action == 'buy' else -total_cost
                created_time = fill.get('created_time', '')

                # Parse timestamp
                try:
                    if created_time:
                        dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = 'Unknown'
                except:
                    time_str = created_time

                print(f"  [{i}] {time_str}")
                print(f"      Market: {ticker}")
                print(f"      Action: {action.upper()} {side.upper()}")
                print(f"      Quantity: {count} contracts @ ${price:.2f}")
                print(f"      Total: ${total_cost:.2f}")
                print()

            print(f"  Net Spent on Recent Fills: ${total_spent:.2f}")

            return fills

        except Exception as e:
            print(f"  ❌ Error checking fills: {e}")
            return []

    async def verify_bot_working(self):
        """Comprehensive verification that bot is working"""
        print("\n" + "="*80)
        print("🔍 BOT VERIFICATION CHECK")
        print("="*80)
        print()

        checks_passed = 0
        checks_total = 6

        # Check 1: API Connection
        print("[1/6] Checking API connection...")
        balance = await self.check_balance()
        if balance is not None:
            print("  ✅ API connection working")
            checks_passed += 1
        else:
            print("  ❌ API connection failed")
        print()

        # Check 2: Database
        print("[2/6] Checking database...")
        try:
            from src.utils.database import DatabaseManager
            db = DatabaseManager()
            await db.initialize()
            print("  ✅ Database initialized")
            checks_passed += 1
        except Exception as e:
            print(f"  ❌ Database error: {e}")
        print()

        # Check 3: Order History
        print("[3/6] Checking order history...")
        orders = await self.check_orders(limit=5, verbose=False)
        if orders:
            print(f"  ✅ Found {len(orders)} orders in history")
            checks_passed += 1
        else:
            print("  ⚠️  No orders found yet")
            print("     This is normal if bot hasn't found opportunities")
        print()

        # Check 4: Recent Fills
        print("[4/6] Checking recent fills (actual trades)...")
        fills = await self.check_fills(limit=5)
        if fills:
            print(f"  ✅ Found {len(fills)} filled trades")
            print("  🎉 BOT HAS SUCCESSFULLY PLACED TRADES!")
            checks_passed += 1
        else:
            print("  ⚠️  No filled trades yet")
            print("     Bot may be:")
            print("       - Waiting for good opportunities")
            print("       - Running in paper mode")
            print("       - Markets are closed/illiquid")
        print()

        # Check 5: Current Positions
        print("[5/6] Checking current positions...")
        positions = await self.check_positions(verbose=False)
        if positions:
            print(f"  ✅ Found {len(positions)} open positions")
            checks_passed += 1
        else:
            print("  ⚠️  No open positions")
            print("     This is normal if bot hasn't entered trades yet")
        print()

        # Check 6: Bot Process
        print("[6/6] Checking if bot is running...")
        import subprocess
        try:
            result = subprocess.run(['pgrep', '-f', 'beast_mode_bot'], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ Bot process is running")
                pids = result.stdout.strip().split('\n')
                print(f"     PIDs: {', '.join(pids)}")
                checks_passed += 1
            else:
                print("  ❌ Bot is NOT running")
                print("     Start it with: python3 beast_mode_bot.py --live")
        except Exception as e:
            print(f"  ⚠️  Could not check bot status: {e}")
        print()

        # Summary
        print("="*80)
        print(f"VERIFICATION SUMMARY: {checks_passed}/{checks_total} checks passed")
        print("="*80)

        if checks_passed >= 5:
            print("✅ Bot appears to be working correctly!")
        elif checks_passed >= 3:
            print("⚠️  Bot is partially working - check warnings above")
        else:
            print("❌ Bot may not be working properly - check errors above")

        print()

    async def watch_trades(self, interval=5):
        """Watch for new trades in real-time"""
        print("\n" + "="*80)
        print("👀 WATCHING FOR NEW TRADES (Press Ctrl+C to stop)")
        print("="*80)
        print()

        # Get initial state
        await self.check_balance()
        initial_orders = await self.check_orders(limit=100, verbose=False)
        initial_positions = await self.check_positions(verbose=False)

        self.last_order_count = len(initial_orders)
        self.last_position_count = len(initial_positions)

        print(f"Starting watch...")
        print(f"  Initial orders: {self.last_order_count}")
        print(f"  Initial positions: {self.last_position_count}")
        print(f"  Checking every {interval} seconds...")
        print()

        try:
            iteration = 0
            while True:
                iteration += 1
                await asyncio.sleep(interval)

                # Check for new orders
                orders = await self.kalshi_client.get_orders()
                current_order_count = len(orders.get('orders', []))

                # Check for new positions
                positions = await self.kalshi_client.get_positions()
                current_position_count = len(positions.get('positions', []))

                # Check balance
                balance_response = await self.kalshi_client.get_balance()
                current_balance = balance_response.get('balance', 0) / 100

                # Detect changes
                new_orders = current_order_count - self.last_order_count
                new_positions = current_position_count - self.last_position_count
                balance_change = current_balance - self.start_balance

                timestamp = datetime.now().strftime('%H:%M:%S')

                if new_orders > 0 or new_positions != 0 or abs(balance_change) > 0.01:
                    print(f"🚨 [{timestamp}] ACTIVITY DETECTED!")
                    if new_orders > 0:
                        print(f"   📝 New orders: +{new_orders} (total: {current_order_count})")
                    if new_positions > 0:
                        print(f"   📊 New positions: +{new_positions} (total: {current_position_count})")
                    elif new_positions < 0:
                        print(f"   ✅ Closed positions: {new_positions} (total: {current_position_count})")
                    if abs(balance_change) > 0.01:
                        sign = "+" if balance_change > 0 else ""
                        print(f"   💰 Balance change: {sign}${balance_change:.2f} (now: ${current_balance:.2f})")
                    print()

                    # Update counts
                    self.last_order_count = current_order_count
                    self.last_position_count = current_position_count
                    self.start_balance = current_balance
                elif iteration % 12 == 0:  # Print status every minute
                    print(f"[{timestamp}] Monitoring... (Orders: {current_order_count}, Positions: {current_position_count}, Balance: ${current_balance:.2f})")

        except KeyboardInterrupt:
            print()
            print("👋 Stopping watch mode...")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Monitor Kalshi trading bot activity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 monitor_trades.py --check-balance    # Check current balance
  python3 monitor_trades.py --check-positions  # Check open positions
  python3 monitor_trades.py --check-trades     # Check recent trades
  python3 monitor_trades.py --watch            # Watch for new trades
  python3 monitor_trades.py --verify           # Full verification check
        """
    )

    parser.add_argument('--check-balance', action='store_true', help='Check account balance')
    parser.add_argument('--check-positions', action='store_true', help='Check current positions')
    parser.add_argument('--check-trades', action='store_true', help='Check recent trades')
    parser.add_argument('--check-fills', action='store_true', help='Check filled orders')
    parser.add_argument('--watch', action='store_true', help='Watch for new trades in real-time')
    parser.add_argument('--verify', action='store_true', help='Run full verification check')
    parser.add_argument('--interval', type=int, default=5, help='Watch interval in seconds (default: 5)')

    args = parser.parse_args()

    # Create monitor
    monitor = TradeMonitor()
    await monitor.initialize()

    try:
        if args.check_balance:
            await monitor.check_balance()
        elif args.check_positions:
            await monitor.check_positions()
        elif args.check_trades:
            await monitor.check_orders()
        elif args.check_fills:
            await monitor.check_fills()
        elif args.watch:
            await monitor.watch_trades(interval=args.interval)
        elif args.verify:
            await monitor.verify_bot_working()
        else:
            # Default: show everything
            await monitor.check_balance()
            await monitor.check_positions()
            await monitor.check_orders()
            await monitor.check_fills()
            print()
            print("💡 TIP: Use --verify for full bot check")
            print("💡 TIP: Use --watch to monitor in real-time")

    finally:
        await monitor.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
