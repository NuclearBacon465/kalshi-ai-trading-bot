#!/bin/bash

# 🚀 Kalshi Trading System - Commands Script
# Quick access to all main commands

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper function
print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${CYAN}🚀 Kalshi Trading System - Commands${NC}"
    echo ""
    echo "Usage: ./commands.sh [COMMAND]"
    echo ""
    echo "MAIN COMMANDS:"
    echo "  trade           - Run the main trading bot"
    echo "  test            - Run interactive test suite"
    echo "  test-quick      - Run quick tests only"
    echo "  test-full       - Run full tests with API calls"
    echo "  positions       - Show current positions"
    echo "  balance         - Show account balance"
    echo "  dashboard       - Launch trading dashboard"
    echo "  performance     - Run performance analysis"
    echo ""
    echo "UTILITY COMMANDS:"
    echo "  config          - Show current configuration"
    echo "  limits          - Check position limits status" 
    echo "  cash            - Check cash reserves status"
    echo "  safe-status     - Check safe mode status"
    echo "  safe-reset      - Reset safe mode (manual override)"
    echo "  logs            - View recent logs"
    echo "  clean           - Clean test files"
    echo "  stop            - Emergency stop trading"
    echo ""
    echo "EXAMPLES:"
    echo "  ./commands.sh trade        # Start trading"
    echo "  ./commands.sh test         # Run tests"
    echo "  ./commands.sh positions    # Check positions"
    echo "  ./commands.sh config       # View settings"
}

# Main trading commands
run_trading() {
    print_header "Starting Beast Mode Trading System"
    python beast_mode_bot.py
}

run_tests() {
    print_header "Running Interactive Test Suite"
    python run_tests.py
}

run_quick_tests() {
    print_header "Running Quick Tests (30 seconds)"
    echo "1" | python run_tests.py
}

run_full_tests() {
    print_header "Running Full Tests (2-3 minutes)"
    echo "2" | python run_tests.py
}

# Position and balance commands
show_positions() {
    print_header "Current Positions"
    python get_positions.py
}

show_balance() {
    print_header "Account Balance"
    python -c "
import asyncio
from src.clients.kalshi_client import KalshiClient
async def main():
    client = KalshiClient()
    try:
        balance = await client.get_balance()
        positions = await client.get_positions()
        print(f'💰 Cash: \${balance.get(\"balance\", 0) / 100:.2f}')
        print(f'📊 Open positions: {len(positions.get(\"positions\", []))}')
    finally:
        await client.close()
asyncio.run(main())
"
}

# Configuration and status
show_config() {
    print_header "Current Configuration"
    python -c "
from src.config.settings import settings
print(f'🎯 Trading Configuration:')
print(f'   Max position size: {settings.trading.max_position_size_pct}%')
print(f'   Max positions: {settings.trading.max_positions}')
print(f'   Min confidence: {settings.trading.min_confidence_to_trade}')
print(f'   Min volume: {settings.trading.min_volume:,}')
print(f'   Kelly fraction: {settings.trading.kelly_fraction}')
print(f'   Primary model: {settings.trading.primary_model}')
print(f'🛡️ Conservative Mode: ENABLED')
print(f'   Min edge required: 15% (up from 10%)')
print(f'   Cash reserves: 1% (down from 15% for full portfolio use)')
"
}

check_position_limits() {
    print_header "Position Limits Status"
    python -c "
import asyncio
from src.utils.position_limits import PositionLimitsManager
from src.utils.database import DatabaseManager
from src.clients.kalshi_client import KalshiClient
async def main():
    db = DatabaseManager()
    await db.initialize()
    kalshi = KalshiClient()
    try:
        manager = PositionLimitsManager(db, kalshi)
        status = await manager.get_position_limits_status()
        print(f'📊 Status: {status[\"status\"]}')
        print(f'📊 Usage: {status[\"position_utilization\"]}')
        print(f'💰 Portfolio value: \${status[\"portfolio_value\"]:.2f}')
        print(f'💰 Available cash: \${status[\"available_cash\"]:.2f}')
        print(f'📏 Max position size: \${status[\"max_position_size\"]:.2f}')
    finally:
        await kalshi.close()
asyncio.run(main())
"
}

check_cash_reserves() {
    print_header "Cash Reserves Status"
    python -c "
import asyncio
from src.utils.cash_reserves import CashReservesManager
from src.utils.database import DatabaseManager
from src.clients.kalshi_client import KalshiClient
async def main():
    db = DatabaseManager()
    await db.initialize()
    kalshi = KalshiClient()
    try:
        manager = CashReservesManager(db, kalshi)
        status = await manager.get_cash_status()
        print(f'💰 Status: {status[\"status\"]}')
        print(f'💰 Reserve %: {status[\"reserve_percentage\"]:.1f}%')
        print(f'💰 Current cash: \${status[\"current_cash\"]:.2f}')
        print(f'📊 Portfolio value: \${status[\"portfolio_value\"]:.2f}')
        print(f'🎯 Target: {status[\"optimal_target\"]}% optimal')
    finally:
        await kalshi.close()
asyncio.run(main())
"
}

check_safe_mode() {
    print_header "Safe Mode Status"
    python -c "
from src.utils.database import DatabaseManager
db = DatabaseManager()
state = db._load_safe_mode_state()
status = 'ACTIVE' if state.get('safe_mode') else 'INACTIVE'
print(f'🛡️ Safe mode: {status}')
print(f'❌ Failure count: {state.get(\"failure_count\", 0)}')
print(f'🕒 Last failure: {state.get(\"last_failure\", \"None\")}')
"
}

reset_safe_mode() {
    print_header "Reset Safe Mode"
    python -c "
from src.utils.database import DatabaseManager
db = DatabaseManager()
db.reset_safe_mode()
print('✅ Safe mode reset. Trading can resume.')
"
}

# Dashboard and analysis
launch_dashboard() {
    print_header "Launching Trading Dashboard"
    python beast_mode_dashboard.py
}

run_performance_analysis() {
    print_header "Running Performance Analysis"
    python -c "
import asyncio
from src.jobs.automated_performance_analyzer import AutomatedPerformanceAnalyzer
async def main():
    analyzer = AutomatedPerformanceAnalyzer()
    result = await analyzer.run_full_analysis()
    print('Performance analysis completed')
asyncio.run(main())
"
}

# Utility functions
view_logs() {
    print_header "Recent Logs"
    if [ -f "logs/latest.log" ]; then
        echo "📄 Last 20 lines from latest.log:"
        tail -20 logs/latest.log
        echo ""
        echo "🔍 Recent edge filtering:"
        grep "EDGE FILTERED" logs/latest.log | tail -5 || echo "No edge filtering found"
        echo ""
        echo "💰 Recent positions:"
        grep "POSITION" logs/latest.log | tail -5 || echo "No position activity found"
    else
        print_warning "No logs found in logs/latest.log"
    fi
}

clean_files() {
    print_header "Cleaning Test Files"
    rm -f test_*.db e2e_test_*.db
    print_success "Cleaned test database files"
    
    if [ -d "__pycache__" ]; then
        rm -rf __pycache__
        print_success "Cleaned Python cache"
    fi
    
    if [ -d ".pytest_cache" ]; then
        rm -rf .pytest_cache
        print_success "Cleaned pytest cache"
    fi
}

emergency_stop() {
    print_header "Emergency Stop"
    print_warning "Stopping all trading processes..."
    
    # Kill any beast mode processes
    pkill -f "python.*beast_mode" 2>/dev/null || true
    pkill -f "beast_mode_bot.py" 2>/dev/null || true
    
    print_success "All trading processes stopped"
    
    # Show any remaining Python processes
    echo ""
    echo "🔍 Remaining Python processes:"
    ps aux | grep python | grep -v grep || echo "No Python processes found"
}

# Main command dispatcher
case "${1:-help}" in
    "trade")
        run_trading
        ;;
    "test")
        run_tests
        ;;
    "test-quick")
        run_quick_tests
        ;;
    "test-full")
        run_full_tests
        ;;
    "positions")
        show_positions
        ;;
    "balance")
        show_balance
        ;;
    "config")
        show_config
        ;;
    "limits")
        check_position_limits
        ;;
    "cash")
        check_cash_reserves
        ;;
    "safe-status")
        check_safe_mode
        ;;
    "safe-reset")
        reset_safe_mode
        ;;
    "dashboard")
        launch_dashboard
        ;;
    "performance")
        run_performance_analysis
        ;;
    "logs")
        view_logs
        ;;
    "clean")
        clean_files
        ;;
    "stop")
        emergency_stop
        ;;
    "help"|*)
        show_usage
        ;;
esac 
