#!/bin/bash
# Upload status to a publicly accessible URL

cd /home/user/kalshi-ai-trading-bot

# Generate status in JSON format for easy parsing
python3 << 'PYEOF'
import asyncio, sys, json
from datetime import datetime
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')

async def get_json_status():
    from src.clients.kalshi_client import KalshiClient
    import sqlite3
    
    status = {"timestamp": datetime.now().isoformat(), "bot_running": True}
    
    # Get account
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        status["cash"] = balance.get('balance', 0) / 100
        status["total"] = balance.get('portfolio_value', 0) / 100
    except Exception as e:
        status["error"] = str(e)
    finally:
        await client.close()
    
    # Get recent AI activity
    conn = sqlite3.connect('trading_system.db')
    c = conn.cursor()
    c.execute("""
        SELECT confidence_extracted, decision_extracted, market_id, timestamp
        FROM llm_queries
        WHERE confidence_extracted IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    analyses = c.fetchall()
    status["recent_analyses"] = [
        {"confidence": conf, "decision": dec, "market": market[:50], "time": ts}
        for conf, dec, market, ts in analyses
    ]
    conn.close()
    
    print(json.dumps(status, indent=2))

asyncio.run(get_json_status())
PYEOF
