#!/usr/bin/env python3
"""
LIVE BOT MONITOR - Run this to watch your bot in real-time!
Usage: python3 monitor_bot.py
"""

import sqlite3
import time
import os
from datetime import datetime, timedelta

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_bot_stats():
    conn = sqlite3.connect('trading_system.db')
    cursor = conn.cursor()

    stats = {}

    # Bot basics
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
    stats['open_positions'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trade_logs")
    stats['total_trades'] = cursor.fetchone()[0]

    # AI activity (last hour)
    cursor.execute("""
        SELECT COUNT(*) FROM llm_queries
        WHERE datetime(timestamp) > datetime('now', '-1 hour')
    """)
    stats['ai_queries_hour'] = cursor.fetchone()[0]

    # Markets
    cursor.execute("SELECT COUNT(*) FROM markets WHERE volume >= 100")
    stats['eligible_markets'] = cursor.fetchone()[0]

    # Recent AI analyses with confidence
    cursor.execute("""
        SELECT market_id, confidence_extracted, decision_extracted, timestamp
        FROM llm_queries
        WHERE confidence_extracted IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    stats['recent_analyses'] = cursor.fetchall()

    # Get positions if any
    cursor.execute("""
        SELECT market_id, side, entry_price, current_pnl, created_at
        FROM positions
        WHERE status = 'open'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    stats['positions'] = cursor.fetchall()

    # Trading opportunities found
    cursor.execute("""
        SELECT COUNT(*) FROM llm_queries
        WHERE decision_extracted IN ('BUY', 'BUY_YES', 'BUY_NO')
        AND datetime(timestamp) > datetime('now', '-1 hour')
    """)
    stats['opportunities_found'] = cursor.fetchone()[0]

    conn.close()
    return stats

def display_dashboard():
    while True:
        try:
            clear_screen()
            stats = get_bot_stats()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print("=" * 80)
            print(f"🤖 KALSHI AI TRADING BOT - LIVE MONITOR".center(80))
            print(f"Last Updated: {now}".center(80))
            print("=" * 80)
            print()

            # Overview
            print("📊 BOT STATUS:")
            print(f"   💰 Open Positions: {stats['open_positions']}")
            print(f"   📈 Total Trades: {stats['total_trades']}")
            print(f"   🧠 AI Queries (last hour): {stats['ai_queries_hour']}")
            print(f"   🎯 Opportunities Found (last hour): {stats['opportunities_found']}")
            print(f"   📊 Eligible Markets: {stats['eligible_markets']}")
            print()

            # Recent AI analyses
            if stats['recent_analyses']:
                print("🧠 RECENT AI ANALYSES:")
                for analysis in stats['recent_analyses']:
                    market, conf, decision, ts = analysis
                    conf_str = f"{conf:.0%}" if conf else "N/A"
                    decision_str = decision or "SKIP"
                    market_short = market[:40] + "..." if len(market) > 40 else market
                    print(f"   {ts} | {decision_str:8} | Conf: {conf_str:5} | {market_short}")
                print()

            # Open positions
            if stats['positions']:
                print("💼 OPEN POSITIONS:")
                for pos in stats['positions']:
                    market, side, entry, pnl, created = pos
                    pnl_str = f"${pnl:.2f}" if pnl else "$0.00"
                    market_short = market[:35] + "..." if len(market) > 35 else market
                    print(f"   {created} | {side:3} | Entry: {entry}¢ | PnL: {pnl_str} | {market_short}")
                print()
            else:
                print("💼 NO OPEN POSITIONS YET")
                print("   Bot is analyzing markets and looking for opportunities...")
                print()

            # Status
            print("=" * 80)
            print("✅ Bot is RUNNING | Press Ctrl+C to exit monitor".center(80))
            print("=" * 80)

            # Refresh every 5 seconds
            time.sleep(5)

        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped. Bot is still running in background!")
            break
        except Exception as e:
            print(f"\n⚠️  Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("🚀 Starting Live Bot Monitor...")
    print("   This will refresh every 5 seconds")
    print("   Press Ctrl+C to stop monitoring\n")
    time.sleep(2)
    display_dashboard()
