#!/bin/bash
# Generate a simple status report you can view

cd /home/user/kalshi-ai-trading-bot

echo "================================================================================"
echo "🤖 KALSHI BOT STATUS REPORT - $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# Bot process status
BOT_PID=$(pgrep -f "beast_mode_bot.py" | head -1)
if [ -n "$BOT_PID" ]; then
    echo "✅ Bot Status: RUNNING (PID: $BOT_PID)"
    echo ""
else
    echo "❌ Bot Status: STOPPED"
    exit 1
fi

# Account status via Python
python3 << 'PYEOF'
import asyncio, sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

async def get_status():
    from src.clients.kalshi_client import KalshiClient
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        total = balance.get('portfolio_value', 0) / 100
        print(f'💰 Account Balance:')
        print(f'   Cash:  ${cash:>10.2f}')
        print(f'   Total: ${total:>10.2f}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await client.close()

asyncio.run(get_status())
PYEOF

echo ""

# Recent AI activity from database
python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect('trading_system.db')
c = conn.cursor()

c.execute("""
    SELECT COUNT(*) FROM llm_queries 
    WHERE datetime(timestamp) > datetime('now', '-10 minutes')
""")
recent = c.fetchone()[0]

c.execute("""
    SELECT confidence_extracted, decision_extracted, market_id, timestamp
    FROM llm_queries
    WHERE confidence_extracted IS NOT NULL
    ORDER BY timestamp DESC
    LIMIT 5
""")
analyses = c.fetchall()

print(f'🧠 AI Activity (last 10 min): {recent} queries')
print('')

if analyses:
    print('Recent Analyses:')
    for conf, decision, market, ts in analyses:
        conf_str = f'{int(conf*100)}%' if conf else 'N/A'
        market_short = (market[:45] + '...') if market and len(market) > 45 else market
        print(f'  [{ts[-8:]}] Confidence: {conf_str:>3} | {decision or "SKIP":8} | {market_short}')

conn.close()
PYEOF

echo ""
echo "================================================================================"
echo "Updated: $(date '+%H:%M:%S')"
echo "================================================================================"
