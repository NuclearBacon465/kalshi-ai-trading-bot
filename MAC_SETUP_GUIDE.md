# 🚀 Mac Setup Guide - Kalshi AI Trading Bot

**Complete guide to run the HIGH RISK HIGH REWARD bot locally on your Mac**

---

## ✅ Prerequisites

### 1. Python 3.11+
```bash
# Check Python version
python3 --version

# If you need to install Python:
brew install python@3.11
```

### 2. Git
```bash
# Check if git is installed
git --version

# If needed:
brew install git
```

---

## 📦 Installation Steps

### Step 1: Clone the Repository
```bash
# Clone the repo
git clone https://github.com/NuclearBacon465/kalshi-ai-trading-bot.git
cd kalshi-ai-trading-bot

# Switch to the working branch
git checkout claude/fix-python-bot-pSI7v
```

### Step 2: Install Python Dependencies
```bash
# Install required packages
pip3 install aiohttp aiosqlite cryptography pydantic python-dotenv structlog

# Or use requirements.txt if available:
pip3 install -r requirements.txt
```

### Step 3: Set Up API Keys

Create a `.env` file in the project root:

```bash
# Create .env file
nano .env
```

Add your API keys (replace with your actual keys):

```.env
# Kalshi API Keys
KALSHI_API_KEY=your-kalshi-api-key-here

# xAI API Key (for Grok AI)
XAI_API_KEY=your-xai-api-key-here
```

**Get your keys:**
- **Kalshi API Key**: https://kalshi.com/account/api-keys
- **xAI API Key**: https://x.ai/api

### Step 4: Add Private Key File

You need your Kalshi private key file:

```bash
# Copy your Kalshi private key to the project root
# Name it: kalshi_private_key

# Set proper permissions
chmod 600 kalshi_private_key
```

**Note:** This file should NOT be committed to git (it's in `.gitignore`)

### Step 5: Verify Database

The database file (`trading_system.db`) should already be in the repo. If not:

```bash
# The bot will create it automatically on first run
# You can also copy it from the server if you have positions
```

---

## 🧪 Testing the Setup

### Run Comprehensive Tests

```bash
# Test API connectivity, orders, profit features
python3 test_buy_sell_profit.py
```

**Expected output:**
```
✅ PASS - Buy Functionality
✅ PASS - Sell Functionality
✅ PASS - Profit Optimization
✅ PASS - Mac Compatibility
🎉 ALL TESTS PASSED: 4/4
```

### Test Individual Components

```bash
# Test Kalshi API compliance
python3 test_kalshi_api.py

# Run comprehensive system tests
python3 comprehensive_test.py
```

---

## 🤖 Running the Bot

### Start the Bot

```bash
# Run in foreground (see live output)
python3 beast_mode_bot.py

# Or run in background
nohup python3 beast_mode_bot.py > bot_output.log 2>&1 &

# Check if running
ps aux | grep beast_mode_bot.py
```

### Monitor the Bot

```bash
# Watch live logs
tail -f bot_output.log

# Or use logs/bot_output.log if it exists
tail -f logs/bot_output.log

# Filter for important events
tail -f logs/bot_output.log | grep -E "(TRADE|Position|ERROR|APPROVED)"
```

### Stop the Bot

```bash
# Find the process ID
ps aux | grep beast_mode_bot.py

# Kill it (replace PID with actual process ID)
kill <PID>

# Or force kill
pkill -9 -f beast_mode_bot.py
```

---

## ⚙️ Configuration

### HIGH RISK HIGH REWARD Settings

Current configuration in `src/config/settings.py`:

```python
# Aggressive trading for maximum returns
min_confidence_to_trade: 50%    # Take more trades
kelly_fraction: 0.75            # Bigger position sizes
max_single_position: 40%        # Up to 40% per trade
daily_ai_budget: $20            # Generous AI analysis budget
```

### Modify Settings (if needed)

Edit `src/config/settings.py`:

```bash
nano src/config/settings.py
```

**Key settings to adjust:**
- `min_confidence_to_trade` - Minimum confidence to take trades (50% = aggressive)
- `kelly_fraction` - Position sizing multiplier (0.75 = aggressive, 0.5 = balanced)
- `max_single_position` - Max % of portfolio per trade (0.40 = 40%)

---

## 💰 Trading Features

### Automated Buy/Sell Orders

**BUY Orders (Entry):**
- **Market BUY**: Fast entry at current price (sets yes_price/no_price = 99¢)
- **Limit BUY**: Wait for better price (specify exact price 1-99¢)

**SELL Orders (Exit):**
- **Market SELL**: Quick exit to lock profits (sets yes_price/no_price = 1¢)
- **Limit SELL**: Target specific profit level (specify exact price)

### Automated Profit Protection

**Profit-Taking (25% target):**
- Automatically places sell orders when position gains 25%
- Locks in profits at 2% below current price for fast execution
- Example: Buy at 50¢ → Current 63¢ → Auto-sell at 61¢ (22% profit)

**Stop-Loss (10% protection):**
- Automatically places sell orders when position loses 10%
- Limits downside risk to protect capital
- Example: Buy at 50¢ → Current 45¢ → Auto-sell at 44¢ (12% loss)

### Position Sizing (Kelly Criterion)

**How it works:**
- Calculates optimal position size based on edge and confidence
- Uses 75% Kelly (aggressive growth)
- Max 40% of portfolio per trade
- Example: $100 portfolio, 65% confidence, 15% edge → $20.89 position

---

## 📊 Monitoring & Performance

### Check Account Balance

```bash
python3 << 'EOF'
import asyncio
from src.clients.kalshi_client import KalshiClient

async def check_balance():
    client = KalshiClient()
    balance = await client.get_balance()
    cash = balance.get('balance', 0) / 100
    portfolio = balance.get('portfolio_value', 0) / 100
    print(f"Cash: ${cash:.2f}")
    print(f"Portfolio: ${portfolio:.2f}")
    print(f"Total: ${cash + portfolio:.2f}")
    await client.close()

asyncio.run(check_balance())
EOF
```

### Check Open Positions

```bash
python3 << 'EOF'
import asyncio
from src.clients.kalshi_client import KalshiClient

async def check_positions():
    client = KalshiClient()
    positions = await client.get_positions()
    for pos in positions.get('market_positions', []):
        ticker = pos.get('ticker', '')
        qty = pos.get('position', 0)
        value = pos.get('market_exposure', 0) / 100
        print(f"{ticker}: {qty} contracts = ${value:.2f}")
    await client.close()

asyncio.run(check_positions())
EOF
```

### View Recent Trades

```bash
# Check database for recent activity
python3 << 'EOF'
import aiosqlite
import asyncio

async def check_trades():
    async with aiosqlite.connect('trading_system.db') as db:
        cursor = await db.execute("""
            SELECT market_id, side, quantity, entry_price, status
            FROM positions
            ORDER BY id DESC
            LIMIT 10
        """)
        positions = await cursor.fetchall()
        for market, side, qty, entry, status in positions:
            print(f"[{status}] {side} {qty}x @ ${entry:.3f} - {market[:50]}")

asyncio.run(check_trades())
EOF
```

---

## 🔧 Troubleshooting

### Issue: "API authentication failed"

**Fix:**
```bash
# Check your .env file has correct keys
cat .env | grep API_KEY

# Verify private key file exists and has correct permissions
ls -la kalshi_private_key
chmod 600 kalshi_private_key
```

### Issue: "Database locked" or "Database not found"

**Fix:**
```bash
# Make sure no other bot process is running
pkill -9 -f beast_mode_bot.py

# Check database file exists
ls -la trading_system.db

# If missing, bot will create it automatically
```

### Issue: "ModuleNotFoundError: No module named 'xyz'"

**Fix:**
```bash
# Install missing dependency
pip3 install <module-name>

# Or reinstall all dependencies
pip3 install -r requirements.txt
```

### Issue: "No trades being placed"

**Reasons:**
1. Markets may be closed (off-hours, weekends)
2. No opportunities meeting 50% confidence threshold
3. Cash reserves preventing trades

**Check:**
```bash
# View recent bot activity
tail -100 logs/bot_output.log | grep -E "(confidence|APPROVED|FILTERED)"

# Check available cash
# (See "Check Account Balance" above)
```

---

## 📈 Performance Expectations

### HIGH RISK HIGH REWARD Mode

**Configuration:**
- Confidence: 50%+ (takes more trades vs 60%+)
- Kelly: 0.75 (aggressive position sizing)
- Max Position: 40% (bigger bets)
- Speed: 2-second cycles (high-frequency)

**What this means:**
- **More trades**: Lower confidence threshold = more opportunities
- **Bigger positions**: 75% Kelly + 40% max = significant capital deployment
- **Higher volatility**: Bigger swings in account value
- **Maximum growth potential**: Optimized for returns, not stability

**Profit Protection:**
- Automated 25% profit-taking locks in wins
- Automated 10% stop-loss limits losses
- Kelly sizing prevents over-betting
- Price validation prevents API errors

---

## 🛡️ Safety Features

### All Safety Features Active:

✅ **Price Validation**: All prices clamped 1-99¢ (Kalshi API requirement)
✅ **Order Validation**: Side, action, type all validated before sending
✅ **Profit-Taking**: Automatic sells at 25% gain
✅ **Stop-Loss**: Automatic sells at 10% loss
✅ **Position Limits**: Max 40% of portfolio per trade
✅ **Kelly Criterion**: Scientific position sizing
✅ **Market SELL**: Fixed (was completely broken before)
✅ **Price Bounds**: Stop-loss and profit-taking prices properly clamped

---

## 📝 Summary

### Bot Will Automatically:

1. **Scan markets** every 2 seconds for opportunities
2. **Take trades** at 50%+ confidence (aggressive)
3. **Size positions** using 75% Kelly (optimal growth)
4. **Monitor positions** every 5 seconds
5. **Take profits** at 25% gains (automated)
6. **Stop losses** at 10% losses (automated)
7. **Validate all orders** before sending to Kalshi

### You Get:

✅ HIGH RISK HIGH REWARD configuration
✅ All order types working (buy/sell, market/limit, yes/no)
✅ 100% Kalshi API compliant
✅ Automated profit protection
✅ Mac compatible
✅ Thoroughly tested (ALL 4/4 tests passing)

---

## 🚨 Important Notes

1. **HIGH RISK** means higher potential returns BUT also higher potential losses
2. The bot trades **real money** on your Kalshi account
3. Start with a **small amount** you're comfortable losing
4. **Monitor regularly** especially when starting out
5. Markets can be **volatile** - expect swings
6. **Weekend/off-hours**: Less trading activity

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs: `tail -f logs/bot_output.log`
3. Run tests: `python3 test_buy_sell_profit.py`
4. Verify API keys are correct
5. Ensure all dependencies are installed

---

## ✅ Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Repository cloned
- [ ] Dependencies installed (`pip3 install ...`)
- [ ] `.env` file created with API keys
- [ ] `kalshi_private_key` file added
- [ ] Tests passing (`python3 test_buy_sell_profit.py`)
- [ ] Bot started (`python3 beast_mode_bot.py`)
- [ ] Monitoring active (`tail -f logs/bot_output.log`)

---

**🚀 You're ready to make profits on Kalshi!**

Good luck and trade responsibly! 💰
