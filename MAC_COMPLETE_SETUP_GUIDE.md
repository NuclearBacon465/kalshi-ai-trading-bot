# 🍎 Complete Mac Setup Guide - Kalshi AI Trading Bot

**Complete step-by-step guide to install, configure, and verify your trading bot on Mac**

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Getting API Keys](#getting-api-keys)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Running the Bot](#running-the-bot)
7. [Monitoring Trades](#monitoring-trades)
8. [Dashboard](#dashboard)
9. [Troubleshooting](#troubleshooting)
10. [Daily Checklist](#daily-checklist)

---

## 1. PREREQUISITES

### Required Software

**Python 3.11 or higher**:
```bash
# Check your Python version
python3 --version

# If not installed or version < 3.11, download from:
# https://www.python.org/downloads/
```

**Git**:
```bash
# Check if Git is installed
git --version

# If not installed, download from:
# https://git-scm.com/downloads
```

**Terminal**: Use the built-in Terminal app (Applications → Utilities → Terminal)

---

## 2. GETTING API KEYS

### A. Kalshi API Keys (2 files needed)

**Step 1**: Go to https://kalshi.com/account/api

**Step 2**: Generate API credentials:
- Click "Generate API Key"
- You'll get:
  - **API Key** (36 characters, like: `a1b2c3d4-e5f6-7890-abcd-1234567890ab`)
  - **Private Key** (RSA private key file)

**Step 3**: Save the Private Key:
```bash
# In your terminal, navigate to the bot directory
cd /path/to/kalshi-ai-trading-bot

# Create the private key file
nano kalshi_private_key

# Paste the ENTIRE private key (including -----BEGIN/END-----)
# Press Ctrl+X, then Y, then Enter to save

# Set secure permissions
chmod 600 kalshi_private_key

# Verify permissions
ls -l kalshi_private_key
# Should show: -rw-------  (600)
```

**Step 4**: Save the API Key (you'll use this in `.env` file later)

### B. xAI API Key (Grok)

**Step 1**: Go to https://x.ai/api or https://console.x.ai

**Step 2**: Sign up or log in

**Step 3**: Generate API key:
- Click "Create API Key"
- Copy the key (starts with `xai-` usually)
- **IMPORTANT**: Save it immediately, you can't see it again!

---

## 3. INSTALLATION

### Option A: Automated Installation (Recommended)

```bash
# Navigate to the bot directory
cd /path/to/kalshi-ai-trading-bot

# Run the setup script
./setup_mac.sh
```

The script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Guide you through API key setup
- ✅ Run verification tests

### Option B: Manual Installation

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create logs directory
mkdir -p logs

# 6. Set up API keys (see section 4)
```

---

## 4. CONFIGURATION

### A. Create .env File

```bash
# Create .env file in the bot root directory
nano .env
```

Add these lines (replace with YOUR actual keys):
```bash
KALSHI_API_KEY=your-kalshi-api-key-here
XAI_API_KEY=your-xai-api-key-here
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

### B. Verify Private Key

```bash
# Check the file exists
ls -l kalshi_private_key

# Should output:
# -rw-------  1 yourusername  staff  1234 Jan  7 10:00 kalshi_private_key

# Verify it contains the key
head -2 kalshi_private_key

# Should show:
# -----BEGIN PRIVATE KEY-----
# MIIEvgIBADANBgkqhkiG9w0BAQEFAA...
```

### C. Configuration Files

The bot is pre-configured for **HIGH RISK HIGH REWARD** trading:

**`src/config/settings.py`** key settings:
- `minimum_confidence: 0.50` (50% confidence threshold)
- `kelly_fraction: 0.75` (75% Kelly - aggressive)
- `max_position_size_pct: 40` (40% max per position)
- `daily_ai_budget: 100` ($100 AI budget)
- `edge_filter: 4-8%` (optimized thresholds)

**You can modify these if needed**, but they're already optimized.

---

## 5. VERIFICATION

### A. Quick Verification

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run quick test
python3 test_your_actual_setup.py
```

**Expected output**:
```
✅ Test 1: Kalshi API Connection - PASSED
✅ Test 2: Account Balance Check - PASSED
✅ Test 3: xAI/Grok API Connection - PASSED

🎉 All tests passed!
```

### B. Deep Verification

```bash
# Run deep validation (tests all 7 components)
python3 test_live_trading_deep.py
```

**Expected output**:
```
✅ ALL 7 DEEP TESTS PASSED
Your bot is READY TO TRADE
```

### C. Edge Case Tests

```bash
# Run edge case tests (tests 10 edge cases)
python3 test_edge_cases_and_bugs.py
```

**Expected output**:
```
✅ 10/10 edge case tests PASSED
Your bot handles edge cases robustly!
```

### D. Check Your Balance

```bash
# Check your current Kalshi balance
python3 monitor_trades.py --check-balance
```

**Expected output**:
```
💰 ACCOUNT BALANCE
  Current Balance: $118.05
  Balance (cents): 11805¢
```

---

## 6. RUNNING THE BOT

### A. Paper Trading Mode (TEST FIRST!)

```bash
# Activate virtual environment
source venv/bin/activate

# Run in paper trading mode (no real money)
python3 beast_mode_bot.py

# Keep it running in the terminal
# Press Ctrl+C to stop
```

**What you should see**:
```
🚀 BEAST MODE TRADING BOT STARTED
📊 Trading Mode: PAPER
💰 Daily AI Budget: $100.0
⚡ Features: Market Making + Portfolio Optimization + Dynamic Exits
🔧 Initializing database...
✅ Database initialization complete!
🔄 Starting market ingestion...
🚀 Starting trading and monitoring tasks...
⚡ Beast Mode HIGH-FREQUENCY Cycle #1 (2s intervals)
```

### B. Live Trading Mode (REAL MONEY!)

**⚠️ WARNING**: This uses REAL MONEY!

```bash
# Activate virtual environment
source venv/bin/activate

# Run in live trading mode
python3 beast_mode_bot.py --live

# The bot will warn you:
⚠️  WARNING: LIVE TRADING MODE ENABLED
💰 This will use real money and place actual trades!
🚀 LIVE TRADING MODE CONFIRMED

# Keep it running in the terminal
# Press Ctrl+C to stop
```

### C. Run in Background

```bash
# Run in background (keeps running after you close terminal)
nohup python3 beast_mode_bot.py --live > bot_output.log 2>&1 &

# Check if it's running
ps aux | grep beast_mode_bot

# View live logs
tail -f bot_output.log

# Stop the bot
pkill -f beast_mode_bot
```

---

## 7. MONITORING TRADES

### A. Check if Bot is Placing Trades

**Method 1: Monitor Script** (BEST WAY)
```bash
# Watch for trades in real-time (updates every 5 seconds)
python3 monitor_trades.py --watch

# Output shows new orders, positions, and balance changes:
🚨 [14:23:45] ACTIVITY DETECTED!
   📝 New orders: +2 (total: 102)
   📊 New positions: +1 (total: 1)
   💰 Balance change: -$10.50 (now: $107.55)
```

**Method 2: Full Verification**
```bash
# Run comprehensive verification
python3 monitor_trades.py --verify

# Checks:
# ✅ API connection
# ✅ Database
# ✅ Order history
# ✅ Filled orders
# ✅ Current positions
# ✅ Bot process running
```

**Method 3: Check Balance**
```bash
# Check current balance
python3 monitor_trades.py --check-balance
```

**Method 4: Check Positions**
```bash
# Check open positions
python3 monitor_trades.py --check-positions
```

**Method 5: Check Recent Trades**
```bash
# Check recent filled orders
python3 monitor_trades.py --check-fills
```

### B. How to Know Bot is Working

**Signs Bot IS Working**:
- ✅ New orders appear in order history
- ✅ Positions open and close automatically
- ✅ Balance changes (decreases when buying, increases when selling)
- ✅ Fills appear in trade history
- ✅ Logs show "TRADE EXECUTED" or "Position opened"

**Signs Bot is NOT Working**:
- ❌ No new orders for hours
- ❌ Balance never changes
- ❌ No positions ever open
- ❌ Logs show errors
- ❌ Bot process not running

### C. Check Kalshi Website Directly

**Go to https://kalshi.com**:
1. Log in to your account
2. Go to "Portfolio" → "Activity"
3. You should see recent orders/trades
4. Check if they were placed by the bot (look at timestamps)

**Compare with bot logs**:
```bash
# Check bot logs for trade times
tail -f bot_output.log | grep -i "trade\|order\|position"
```

---

## 8. DASHBOARD

### A. Launch Dashboard

```bash
# Activate virtual environment
source venv/bin/activate

# Launch the dashboard
python3 beast_mode_bot.py --dashboard
```

**What you should see**:
- Real-time performance metrics
- Current positions
- Recent trades
- Profit/loss tracking
- Capital utilization
- Win rate

### B. Dashboard Features

The dashboard shows:
1. **Portfolio Overview**
   - Total balance
   - Position value
   - Available cash
   - Capital utilization

2. **Performance Metrics**
   - Total trades
   - Win rate
   - Average profit
   - Sharpe ratio
   - Max drawdown

3. **Current Positions**
   - Open positions
   - Entry price vs current price
   - Unrealized P/L
   - Time held

4. **Recent Activity**
   - Recent trades
   - Trade outcomes
   - Profit/loss per trade

### C. Dashboard Troubleshooting

**If dashboard doesn't start**:
```bash
# Check if all dependencies are installed
pip install -r requirements.txt

# Check if dashboard file exists
ls -l beast_mode_dashboard.py

# Try running with debug mode
python3 beast_mode_dashboard.py
```

**If dashboard shows no data**:
- Make sure bot has been running for a while
- Check database exists: `ls -l trading_system.db`
- Verify bot has placed trades: `python3 monitor_trades.py --verify`

---

## 9. TROUBLESHOOTING

### Common Issues

#### Issue 1: "Permission denied: kalshi_private_key"
**Solution**:
```bash
chmod 600 kalshi_private_key
```

#### Issue 2: "ModuleNotFoundError"
**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue 3: "API authentication failed"
**Solution**:
```bash
# Check .env file has correct keys
cat .env

# Verify private key format
head -2 kalshi_private_key
# Should start with: -----BEGIN PRIVATE KEY-----

# Test API connection
python3 test_your_actual_setup.py
```

#### Issue 4: "Bot not placing any trades"
**Possible reasons**:
1. **Markets are closed/illiquid** - Bot only trades when markets have liquidity
2. **No opportunities found** - Bot has strict edge requirements (4-8% edge)
3. **Bot in paper mode** - Use `--live` flag for real trading
4. **Daily AI budget exhausted** - Check logs for budget limit warnings

**Check**:
```bash
# Verify bot is in live mode and finding markets
tail -100 bot_output.log | grep -i "market\|opportunity\|edge"

# Check for errors
tail -100 bot_output.log | grep -i "error\|fail"
```

#### Issue 5: "Dashboard not showing data"
**Solution**:
```bash
# Check database exists and has data
sqlite3 trading_system.db "SELECT COUNT(*) FROM trade_logs;"
sqlite3 trading_system.db "SELECT COUNT(*) FROM positions;"

# If empty, bot hasn't traded yet
```

### Getting Help

**Check logs**:
```bash
# View recent logs
tail -100 bot_output.log

# Watch logs in real-time
tail -f bot_output.log

# Search for errors
grep -i error bot_output.log
```

**Run diagnostics**:
```bash
# Full verification
python3 monitor_trades.py --verify

# Check all tests
python3 test_live_trading_deep.py
```

---

## 10. DAILY CHECKLIST

### Morning Routine (5 minutes)

```bash
# 1. Check bot is still running
ps aux | grep beast_mode_bot

# 2. Check balance
python3 monitor_trades.py --check-balance

# 3. Check positions
python3 monitor_trades.py --check-positions

# 4. Check recent fills
python3 monitor_trades.py --check-fills

# 5. Check logs for errors
tail -50 bot_output.log | grep -i error
```

### Evening Review (10 minutes)

```bash
# 1. Full verification
python3 monitor_trades.py --verify

# 2. View dashboard
python3 beast_mode_bot.py --dashboard

# 3. Check daily performance
# - How many trades?
# - Win rate?
# - Profit/loss?

# 4. Compare with Kalshi website
# - Go to https://kalshi.com
# - Check Portfolio → Activity
# - Verify trades match bot logs
```

### Weekly Maintenance (30 minutes)

```bash
# 1. Update code (if needed)
git pull origin main

# 2. Run all tests
python3 test_live_trading_deep.py
python3 test_edge_cases_and_bugs.py

# 3. Review logs for patterns
grep -i "trade\|position" bot_output.log | tail -100

# 4. Backup database
cp trading_system.db backups/trading_system_$(date +%Y%m%d).db

# 5. Review performance
# - Total profit/loss?
# - Average trade size?
# - Strategy working?
```

---

## 📊 QUICK COMMAND REFERENCE

```bash
# SETUP
./setup_mac.sh                              # Automated setup
source venv/bin/activate                     # Activate environment

# TESTING
python3 test_your_actual_setup.py           # Quick test
python3 test_live_trading_deep.py           # Deep validation
python3 test_edge_cases_and_bugs.py         # Edge case tests

# RUNNING
python3 beast_mode_bot.py                   # Paper trading
python3 beast_mode_bot.py --live            # Live trading (REAL MONEY)
python3 beast_mode_bot.py --dashboard       # Dashboard mode

# MONITORING
python3 monitor_trades.py --verify          # Full verification
python3 monitor_trades.py --watch           # Watch in real-time
python3 monitor_trades.py --check-balance   # Check balance
python3 monitor_trades.py --check-positions # Check positions
python3 monitor_trades.py --check-fills     # Check filled orders

# MANAGEMENT
ps aux | grep beast_mode_bot                # Check if running
pkill -f beast_mode_bot                     # Stop bot
tail -f bot_output.log                      # View live logs
```

---

## ✅ VERIFICATION CHECKLIST

Before you start live trading, verify:

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with both API keys
- [ ] `kalshi_private_key` file exists with 600 permissions
- [ ] `test_your_actual_setup.py` passes (3/3 tests)
- [ ] `test_live_trading_deep.py` passes (7/7 tests)
- [ ] `monitor_trades.py --check-balance` shows your balance
- [ ] Bot runs in paper mode without errors
- [ ] `monitor_trades.py --verify` passes (5+/6 checks)

---

## 🎉 YOU'RE READY TO TRADE!

Once all checks pass:

1. **Start small**: Let bot run for a day in live mode
2. **Monitor closely**: Use `--watch` mode to see trades in real-time
3. **Verify trades**: Check Kalshi website matches bot activity
4. **Review daily**: Use the checklist above
5. **Iterate**: Adjust configuration based on performance

**Good luck and happy trading! 💰**

---

## 📞 SUPPORT

**Issues**:
- Check troubleshooting section above
- Run `python3 monitor_trades.py --verify`
- Check logs: `tail -100 bot_output.log`

**Questions**:
- Review `COMPREHENSIVE_BUG_SCAN_REPORT.md`
- Review `DEEP_VALIDATION_COMPLETE.md`
- Check `PROFITABILITY_OPTIMIZATIONS.md`

---

*Last Updated: 2026-01-07*
*Version: 2.0 - Complete Mac Setup Guide*
