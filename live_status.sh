#!/bin/bash
# LIVE BOT STATUS - Run this to see what the bot is doing RIGHT NOW

clear
echo "================================================================================"
echo "                   🤖 KALSHI AI TRADING BOT - LIVE STATUS"
echo "                        Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# Check if bot is running
BOT_PID=$(pgrep -f "beast_mode_bot.py" | head -1)
if [ -n "$BOT_PID" ]; then
    echo "✅ BOT STATUS: RUNNING (PID: $BOT_PID)"
else
    echo "❌ BOT STATUS: NOT RUNNING"
    exit 1
fi

echo ""
echo "================================================================================"
echo "📊 CURRENT ACCOUNT STATUS"
echo "================================================================================"
python3 -c "
import asyncio
import sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

async def quick_status():
    from src.clients.kalshi_client import KalshiClient
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        positions = await client.get_positions()

        cash = balance.get('balance', 0) / 100
        total = balance.get('portfolio_value', 0) / 100
        position_value = total - cash

        print(f'💰 Cash Available: \${cash:.2f}')
        print(f'📈 Position Value: \${position_value:.2f}')
        print(f'💼 Total Portfolio: \${total:.2f}')
        print(f'📊 Open Positions: {len(positions.get(\"market_positions\", []))}')

        if positions.get('market_positions'):
            print('\n   Current Positions:')
            for pos in positions['market_positions'][:5]:
                ticker = pos.get('ticker', 'N/A')[:45]
                qty = pos.get('position', 0)
                val = pos.get('market_exposure', 0) / 100
                print(f'   • {ticker}: {qty} contracts (\${val:.2f})')
    except Exception as e:
        print(f'Error fetching account status: {e}')
    finally:
        await client.close()

asyncio.run(quick_status())
" 2>/dev/null

echo ""
echo "================================================================================"
echo "🧠 AI ACTIVITY (LAST 10 MINUTES)"
echo "================================================================================"
python3 -c "
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('trading_system.db')
c = conn.cursor()

c.execute('''
    SELECT COUNT(*) FROM llm_queries
    WHERE datetime(timestamp) > datetime('now', '-10 minutes')
''')
recent_queries = c.fetchone()[0]

c.execute('''
    SELECT market_id, confidence_extracted, decision_extracted, timestamp
    FROM llm_queries
    WHERE confidence_extracted IS NOT NULL
    AND datetime(timestamp) > datetime('now', '-10 minutes')
    ORDER BY timestamp DESC
    LIMIT 5
''')
analyses = c.fetchall()

print(f'🤖 AI Queries: {recent_queries} in last 10 minutes')
print('')

if analyses:
    print('Recent AI Decisions:')
    for market, conf, decision, ts in analyses:
        market_short = market[:50] + '...' if len(market) > 50 else market
        conf_str = f'{conf*100:.0f}%' if conf else 'N/A'
        print(f'  [{ts}] {decision or \"SKIP\":8} | Confidence: {conf_str:4} | {market_short}')
else:
    print('No recent AI analyses found.')

conn.close()
"

echo ""
echo "================================================================================"
echo "📈 RECENT BOT ACTIVITY (LAST 30 SECONDS)"
echo "================================================================================"
tail -30 logs/bot_output.log | grep -E "TRADE|BUY|SELL|EDGE|APPROVED|FAILED|💰|🚀|✅|❌" | tail -10 || echo "No recent trading activity"

echo ""
echo "================================================================================"
echo "⚡ LIVE LOG STREAM (updating...)"
echo "================================================================================"
echo "Showing last 5 log entries:"
tail -5 logs/bot_output.log | sed 's/\x1b\[[0-9;]*m//g' | cut -d' ' -f4-

echo ""
echo "================================================================================"
echo "💡 TIP: Run 'tail -f logs/bot_output.log' to watch live updates"
echo "💡 TIP: Run 'python3 monitor_bot.py' for auto-refreshing dashboard"
echo "================================================================================"
