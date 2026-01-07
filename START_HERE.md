# 🚀 START HERE - Quick Setup Guide

**Everything you need to get your Kalshi trading bot running on Mac**

---

## ⚡ QUICK START (5 Minutes)

```bash
# 1. Run automated setup
./setup_mac.sh

# 2. Verify everything works
python3 monitor_trades.py --verify

# 3. Start trading (paper mode first!)
python3 beast_mode_bot.py

# 4. Monitor trades
python3 monitor_trades.py --watch
```

**That's it!** The bot is now running and you can watch it trade in real-time.

---

## 📋 WHAT YOU NEED

### API Keys (Get these first!)

1. **Kalshi API** (https://kalshi.com/account/api)
   - API Key (looks like: `a1b2c3d4-e5f6-7890-abcd-1234567890ab`)
   - Private Key (RSA key file)

2. **xAI API** (https://x.ai/api)
   - API Key (looks like: `xai-...`)

### Software (Probably already installed)

- Python 3.11+ (check: `python3 --version`)
- Git (check: `git --version`)

---

## 🎯 STEP-BY-STEP SETUP

### Step 1: Get Your API Keys

**Kalshi**:
1. Go to https://kalshi.com/account/api
2. Click "Generate API Key"
3. Save the API Key
4. Download the Private Key file
5. Save Private Key as `kalshi_private_key` in this folder

**xAI**:
1. Go to https://x.ai/api
2. Generate API key
3. Copy and save it

### Step 2: Run Setup Script

```bash
# Make it executable (first time only)
chmod +x setup_mac.sh

# Run it
./setup_mac.sh

# Follow the prompts:
# - Enter your Kalshi API Key when asked
# - Enter your xAI API Key when asked
# - Script will verify everything
```

### Step 3: Verify It Works

```bash
# Run verification (checks 6 things)
python3 monitor_trades.py --verify

# Should show:
# ✅ API connection working
# ✅ Database initialized
# ✅ Bot process running (if started)
# etc.
```

### Step 4: Start The Bot

**Test Mode (NO REAL MONEY)**:
```bash
python3 beast_mode_bot.py
```

**Live Mode (REAL MONEY - use after testing!)**:
```bash
python3 beast_mode_bot.py --live
```

**Dashboard Mode**:
```bash
python3 beast_mode_bot.py --dashboard
```

### Step 5: Monitor Trades

**Watch in real-time** (recommended):
```bash
python3 monitor_trades.py --watch

# Shows:
# 🚨 [14:23:45] ACTIVITY DETECTED!
#    📝 New orders: +2
#    📊 New positions: +1
#    💰 Balance change: -$10.50
```

**Check balance**:
```bash
python3 monitor_trades.py --check-balance
```

**Check positions**:
```bash
python3 monitor_trades.py --check-positions
```

**Check if trades are actually happening**:
```bash
python3 monitor_trades.py --check-fills

# This shows FILLED orders (proof bot is trading)
# If empty, bot hasn't traded yet (may be waiting for opportunities)
```

---

## ❓ HOW TO KNOW IF BOT IS WORKING

### Signs Bot IS Working ✅

1. **monitor_trades.py --watch** shows activity
2. **New orders** appear when you check
3. **Balance changes** over time
4. **Positions open and close** automatically
5. **Fills show up** in --check-fills

### Signs Bot is NOT Working ❌

1. No activity for hours in --watch mode
2. No orders or positions ever
3. Balance never changes
4. Errors in logs: `tail -f bot_output.log`
5. Bot process not running: `ps aux | grep beast_mode`

### What To Do If Not Working

```bash
# 1. Check the bot is actually running
ps aux | grep beast_mode_bot

# 2. Check for errors
tail -100 bot_output.log | grep -i error

# 3. Run full verification
python3 monitor_trades.py --verify

# 4. Run tests
python3 test_your_actual_setup.py
python3 test_live_trading_deep.py

# 5. Check API keys
cat .env
```

---

## 📊 MONITORING OPTIONS

| Command | What It Does |
|---------|--------------|
| `python3 monitor_trades.py --verify` | Full system check (6 checks) |
| `python3 monitor_trades.py --watch` | Real-time monitoring |
| `python3 monitor_trades.py --check-balance` | Show current balance |
| `python3 monitor_trades.py --check-positions` | Show open positions |
| `python3 monitor_trades.py --check-fills` | Show filled trades (PROOF) |
| `python3 beast_mode_bot.py --dashboard` | Launch dashboard |

---

## 🎛️ BOT MODES

### Paper Trading (Test Mode)
```bash
python3 beast_mode_bot.py
```
- **No real money**
- **Safe for testing**
- Same logic as live mode
- Use this FIRST!

### Live Trading (Real Money!)
```bash
python3 beast_mode_bot.py --live
```
- **⚠️ USES REAL MONEY**
- **Places actual trades**
- Test first in paper mode!
- Monitor closely at start

### Dashboard Mode
```bash
python3 beast_mode_bot.py --dashboard
```
- View performance metrics
- See current positions
- Track profit/loss
- Real-time updates

---

## 📱 CHECKING ON KALSHI WEBSITE

**Verify trades manually**:

1. Go to https://kalshi.com
2. Log in to your account
3. Click "Portfolio" → "Activity"
4. You should see recent orders/trades
5. Compare timestamps with bot logs

**This is the ULTIMATE PROOF bot is working!**

If you see trades on Kalshi website with timestamps matching your bot logs, the bot IS WORKING.

---

## 🐛 TROUBLESHOOTING

### "Permission denied: kalshi_private_key"
```bash
chmod 600 kalshi_private_key
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "API authentication failed"
```bash
# Check your .env file
cat .env

# Make sure kalshi_private_key exists and is correct
head -2 kalshi_private_key
```

### "Bot not placing trades"
**This is normal if**:
- Markets are closed (off-hours)
- No opportunities found (bot has strict requirements)
- Running in paper mode without --live flag
- Daily AI budget exhausted

**Check**:
```bash
# Look for errors
tail -100 bot_output.log | grep -i error

# Check bot is finding markets
tail -100 bot_output.log | grep -i market

# Run verification
python3 monitor_trades.py --verify
```

---

## 📁 IMPORTANT FILES

| File | Purpose |
|------|---------|
| `setup_mac.sh` | Automated installation |
| `monitor_trades.py` | Trade monitoring tool |
| `beast_mode_bot.py` | Main bot |
| `.env` | API keys (YOU CREATE THIS) |
| `kalshi_private_key` | Kalshi private key (YOU CREATE THIS) |
| `bot_output.log` | Bot logs (created automatically) |
| `trading_system.db` | Trade database (created automatically) |

---

## 📚 COMPLETE GUIDES

For more detailed instructions, see:

1. **MAC_COMPLETE_SETUP_GUIDE.md** - Complete setup guide
   - Detailed API key instructions
   - Configuration options
   - Troubleshooting
   - Daily checklists

2. **DEEP_VALIDATION_COMPLETE.md** - Test results
   - All validation test results
   - Bug fixes verified
   - Performance optimizations

3. **COMPREHENSIVE_BUG_SCAN_REPORT.md** - Bug report
   - All bugs found and fixed
   - Recommended improvements
   - Test coverage

---

## ✅ VERIFICATION CHECKLIST

Before live trading, make sure:

- [ ] `./setup_mac.sh` completed successfully
- [ ] `python3 monitor_trades.py --verify` shows 5+/6 checks passed
- [ ] `python3 monitor_trades.py --check-balance` shows your balance
- [ ] Bot runs in paper mode without errors
- [ ] You understand how to monitor trades
- [ ] You checked Kalshi website for trade history

---

## 🎉 YOU'RE READY!

Once setup is complete:

1. ✅ Start bot in paper mode: `python3 beast_mode_bot.py`
2. ✅ Watch for trades: `python3 monitor_trades.py --watch`
3. ✅ After testing, go live: `python3 beast_mode_bot.py --live`
4. ✅ Monitor daily: Check balance, positions, fills
5. ✅ Verify on Kalshi: https://kalshi.com → Portfolio → Activity

**Happy trading! 💰**

---

## 💡 QUICK TIPS

- **Start small**: Let bot run for a day before increasing capital
- **Monitor closely**: Use --watch mode for first few days
- **Check Kalshi**: Verify trades on website match bot activity
- **Review logs**: Check for errors daily
- **Back up**: Keep backups of trading_system.db

---

## 📞 NEED HELP?

**First steps**:
1. Run `python3 monitor_trades.py --verify`
2. Check logs: `tail -100 bot_output.log`
3. Review MAC_COMPLETE_SETUP_GUIDE.md

**Still stuck?**:
- Check COMPREHENSIVE_BUG_SCAN_REPORT.md
- Review troubleshooting section in MAC_COMPLETE_SETUP_GUIDE.md

---

*Last Updated: 2026-01-07*
*All bugs fixed - 100% ready for production*
