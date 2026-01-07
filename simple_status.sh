#!/bin/bash
echo "🤖 BOT STATUS - $(date '+%H:%M:%S')"
echo "Bot: $(pgrep -f beast_mode_bot.py > /dev/null && echo '✅ Running' || echo '❌ Stopped')"
python3 -c "
import asyncio, sys, sqlite3
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')
async def s():
    from src.clients.kalshi_client import KalshiClient
    c = KalshiClient()
    try:
        b = await c.get_balance()
        print(f'💰 ${b.get(\"balance\",0)/100:.2f} cash')
    finally:
        await c.close()
asyncio.run(s())
" 2>/dev/null
