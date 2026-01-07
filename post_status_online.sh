#!/bin/bash
# Post status to a public URL you can access from anywhere

cd /home/user/kalshi-ai-trading-bot

# Generate status report
STATUS=$(cat << 'EOF'
================================================================================
🤖 KALSHI TRADING BOT - LIVE STATUS
Generated: $(date '+%Y-%m-%d %H:%M:%S')
================================================================================

EOF
)

# Add bot status
BOT_PID=$(pgrep -f "beast_mode_bot.py" | head -1)
if [ -n "$BOT_PID" ]; then
    STATUS="${STATUS}\n✅ Bot Running (PID: $BOT_PID)\n\n"
else
    STATUS="${STATUS}\n❌ Bot Stopped\n\n"
fi

# Add account and AI status
STATUS="${STATUS}$(python3 << 'PYEOF'
import asyncio, sys, sqlite3
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

async def get_all():
    from src.clients.kalshi_client import KalshiClient
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        cash = balance.get('balance', 0) / 100
        total = balance.get('portfolio_value', 0) / 100
        print(f'💰 Account: ${cash:.2f} cash | ${total:.2f} total\n')
    finally:
        await client.close()
    
    conn = sqlite3.connect('trading_system.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM llm_queries WHERE datetime(timestamp) > datetime('now', '-10 minutes')")
    recent = c.fetchone()[0]
    print(f'🧠 AI Queries (10min): {recent}\n')
    
    c.execute("""
        SELECT confidence_extracted, decision_extracted, market_id, timestamp
        FROM llm_queries WHERE confidence_extracted IS NOT NULL
        ORDER BY timestamp DESC LIMIT 8
    """)
    print('Recent AI Decisions:')
    for conf, dec, market, ts in c.fetchall():
        conf_str = f'{int(conf*100)}%' if conf else 'N/A'
        market_short = market[:50] if market else 'Unknown'
        print(f'  [{ts[-8:]}] {conf_str:>3} conf | {dec or "SKIP":8} | {market_short}')
    conn.close()

asyncio.run(get_all())
PYEOF
)"

# Post to public pastebin (ix.io)
echo -e "$STATUS" | curl -F 'f:1=<-' ix.io
