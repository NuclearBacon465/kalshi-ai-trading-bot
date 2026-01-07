#!/bin/bash
# Ultra-simple status display - no web server needed!

echo "================================================================================"
echo "                    KALSHI BOT STATUS - $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# Account info from API
echo "💰 ACCOUNT STATUS:"
python3 << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

async def get_status():
    from src.clients.kalshi_client import KalshiClient
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        positions = await client.get_positions()

        cash = balance.get('balance', 0) / 100
        total = balance.get('portfolio_value', 0) / 100
        pos_val = total - cash

        print(f'   Cash:      ${cash:>8.2f}')
        print(f'   Positions: ${pos_val:>8.2f}')
        print(f'   Total:     ${total:>8.2f}')
        print(f'   Open:      {len(positions.get("market_positions", []))} positions')

        if positions.get('market_positions'):
            print('\n📊 POSITIONS:')
            for pos in positions['market_positions'][:3]:
                ticker = pos['ticker'][:50]
                qty = pos['position']
                val = pos['market_exposure'] / 100
                print(f'   • {ticker}')
                print(f'     {qty} contracts = ${val:.2f}')
    except Exception as e:
        print(f'   Error: {e}')
    finally:
        await client.close()

asyncio.run(get_status())
PYEOF

echo ""
echo "🤖 BOT ACTIVITY:"
python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect('trading_system.db')
c = conn.cursor()

# AI queries
c.execute("SELECT COUNT(*) FROM llm_queries WHERE datetime(timestamp) > datetime('now', '-1 hour')")
queries = c.fetchone()[0]

# Markets
c.execute("SELECT COUNT(*) FROM markets WHERE volume >= 100")
markets = c.fetchone()[0]

# Recent decisions
c.execute("""
    SELECT decision_extracted, COUNT(*)
    FROM llm_queries
    WHERE datetime(timestamp) > datetime('now', '-1 hour')
    AND decision_extracted IS NOT NULL
    GROUP BY decision_extracted
""")
decisions = c.fetchall()

print(f'   AI Queries (1hr): {queries}')
print(f'   Markets Scanned:  {markets}')
if decisions:
    print('   Decisions:')
    for dec, count in decisions:
        print(f'     {dec}: {count}')

conn.close()
PYEOF

echo ""
echo "⚡ RECENT ACTIVITY (last 10 log lines):"
tail -10 logs/bot_output.log | sed 's/\x1b\[[0-9;]*m//g' | grep -E "TRADE|EDGE|Portfolio|Cycle" | tail -5 || echo "   No recent trading activity"

echo ""
echo "================================================================================"
echo "✅ Bot is running - Use './watch_bot.sh' for live updates"
echo "================================================================================"
