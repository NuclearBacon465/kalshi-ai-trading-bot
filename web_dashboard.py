#!/usr/bin/env python3
"""
Simple Web Dashboard for Kalshi Trading Bot
Access from your browser at: http://your-server-ip:8080

Run with: python3 web_dashboard.py
"""

import asyncio
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import sys
sys.path.insert(0, '/home/user/kalshi-ai-trading-bot')
from src.clients.kalshi_client import KalshiClient

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Kalshi Trading Bot Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            background: #10b981;
            color: white;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #667eea;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .stat:last-child { border-bottom: none; }
        .stat-label {
            font-weight: 600;
            color: #666;
        }
        .stat-value {
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }
        .positive { color: #10b981 !important; }
        .negative { color: #ef4444 !important; }
        .activity-item {
            padding: 12px;
            background: #f8fafc;
            border-left: 3px solid #667eea;
            margin-bottom: 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .activity-time {
            color: #666;
            font-size: 0.85em;
            margin-bottom: 5px;
        }
        .position-item {
            padding: 15px;
            background: #f0fdf4;
            border-left: 3px solid #10b981;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .position-ticker {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .position-details {
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #666;
        }
        .refresh-notice {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulse { animation: pulse 2s ease-in-out infinite; }
    </style>
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                // Update account stats
                document.getElementById('cash').textContent = '$' + data.account.cash.toFixed(2);
                document.getElementById('portfolio').textContent = '$' + data.account.total.toFixed(2);
                document.getElementById('position-value').textContent = '$' + data.account.position_value.toFixed(2);
                document.getElementById('position-count').textContent = data.account.open_positions;

                // Update bot stats
                document.getElementById('ai-queries').textContent = data.bot.ai_queries_hour;
                document.getElementById('opportunities').textContent = data.bot.opportunities_found;
                document.getElementById('markets').textContent = data.bot.eligible_markets;

                // Update positions
                const positionsDiv = document.getElementById('positions');
                if (data.positions.length > 0) {
                    positionsDiv.innerHTML = data.positions.map(pos => `
                        <div class="position-item">
                            <div class="position-ticker">${pos.ticker}</div>
                            <div class="position-details">
                                <span>${pos.quantity} contracts</span>
                                <span>$${pos.value.toFixed(2)}</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    positionsDiv.innerHTML = '<div class="activity-item">No open positions</div>';
                }

                // Update recent activity
                const activityDiv = document.getElementById('activity');
                if (data.activity.length > 0) {
                    activityDiv.innerHTML = data.activity.map(act => `
                        <div class="activity-item">
                            <div class="activity-time">${act.time}</div>
                            <div>${act.message}</div>
                        </div>
                    `).join('');
                } else {
                    activityDiv.innerHTML = '<div class="activity-item">No recent activity</div>';
                }

                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }

        // Refresh every 5 seconds
        setInterval(refreshData, 5000);

        // Initial load
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Kalshi Trading Bot</h1>
            <span class="status-badge">● LIVE</span>
            <p style="margin-top: 10px; color: #666;">Real-time monitoring dashboard</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>💰 Account Status</h2>
                <div class="stat">
                    <span class="stat-label">Cash Available</span>
                    <span class="stat-value positive" id="cash">Loading...</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Position Value</span>
                    <span class="stat-value" id="position-value">Loading...</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Portfolio</span>
                    <span class="stat-value" id="portfolio">Loading...</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Open Positions</span>
                    <span class="stat-value" id="position-count">Loading...</span>
                </div>
            </div>

            <div class="card">
                <h2>🤖 Bot Activity</h2>
                <div class="stat">
                    <span class="stat-label">AI Queries (1hr)</span>
                    <span class="stat-value" id="ai-queries">Loading...</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Opportunities Found</span>
                    <span class="stat-value" id="opportunities">Loading...</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Eligible Markets</span>
                    <span class="stat-value" id="markets">Loading...</span>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>📊 Current Positions</h2>
                <div id="positions" class="loading pulse">Loading positions...</div>
            </div>

            <div class="card">
                <h2>⚡ Recent Activity</h2>
                <div id="activity" class="loading pulse">Loading activity...</div>
            </div>
        </div>

        <div class="refresh-notice">
            Auto-refreshing every 5 seconds | Last update: <span id="last-update">-</span>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    """API endpoint that returns current bot status."""
    try:
        # Get data from database
        conn = sqlite3.connect('trading_system.db')
        c = conn.cursor()

        # AI activity
        c.execute("""
            SELECT COUNT(*) FROM llm_queries
            WHERE datetime(timestamp) > datetime('now', '-1 hour')
        """)
        ai_queries = c.fetchone()[0]

        # Opportunities found
        c.execute("""
            SELECT COUNT(*) FROM llm_queries
            WHERE decision_extracted IN ('BUY', 'BUY_YES', 'BUY_NO')
            AND datetime(timestamp) > datetime('now', '-1 hour')
        """)
        opportunities = c.fetchone()[0]

        # Eligible markets
        c.execute("SELECT COUNT(*) FROM markets WHERE volume >= 100")
        markets = c.fetchone()[0]

        # Recent activity
        c.execute("""
            SELECT market_id, confidence_extracted, decision_extracted, timestamp
            FROM llm_queries
            WHERE confidence_extracted IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        activity_data = c.fetchall()

        conn.close()

        # Get account data from Kalshi
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        account_data = loop.run_until_complete(get_account_data())
        loop.close()

        # Format activity
        activity = []
        for market, conf, decision, ts in activity_data:
            activity.append({
                'time': ts,
                'message': f"{decision or 'SKIP'} - {market[:50]}... (Confidence: {int(conf*100) if conf else 0}%)"
            })

        return jsonify({
            'account': account_data['account'],
            'positions': account_data['positions'],
            'bot': {
                'ai_queries_hour': ai_queries,
                'opportunities_found': opportunities,
                'eligible_markets': markets
            },
            'activity': activity
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def get_account_data():
    """Fetch account data from Kalshi API."""
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        positions = await client.get_positions()

        cash = balance.get('balance', 0) / 100
        total = balance.get('portfolio_value', 0) / 100
        position_value = total - cash

        position_list = []
        for pos in positions.get('market_positions', [])[:10]:
            position_list.append({
                'ticker': pos.get('ticker', 'N/A'),
                'quantity': pos.get('position', 0),
                'value': pos.get('market_exposure', 0) / 100
            })

        return {
            'account': {
                'cash': cash,
                'total': total,
                'position_value': position_value,
                'open_positions': len(positions.get('market_positions', []))
            },
            'positions': position_list
        }
    finally:
        await client.close()

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Starting Kalshi Trading Bot Web Dashboard")
    print("=" * 80)
    print("\n📡 Dashboard will be available at:")
    print("   - Local:  http://localhost:8080")
    print("   - Remote: http://YOUR-SERVER-IP:8080")
    print("\n💡 To access from your Mac:")
    print("   1. Find your server's IP address")
    print("   2. Open browser and go to: http://YOUR-SERVER-IP:8080")
    print("\n⏹️  Press Ctrl+C to stop the dashboard")
    print("=" * 80)
    print()

    app.run(host='0.0.0.0', port=8080, debug=False)
