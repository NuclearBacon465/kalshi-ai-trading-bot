#!/bin/bash
# WATCH BOT LIVE - Continuously monitor bot activity

echo "🤖 WATCHING BOT LIVE - Press Ctrl+C to stop"
echo "Filtering for: Trading decisions, AI analysis, and important events"
echo "================================================================================"
echo ""

tail -f logs/bot_output.log | grep --line-buffered -E "EDGE|TRADE|BUY|SELL|APPROVED|FAILED|CASH|POSITION|Portfolio|💰|🚀|✅|❌|🎯|Cycle|Started" | while read line; do
    echo "[$(date '+%H:%M:%S')] $line" | sed 's/\x1b\[[0-9;]*m//g'
done
